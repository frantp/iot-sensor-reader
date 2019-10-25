from collections import OrderedDict
import struct
import sys
import time

from ..core import SMBusDriver, run_drivers, round_step
from smbus2 import SMBus

import RPi.GPIO as GPIO


# Designed to work with arduino-vertpantilt:
# https://github.com/frantp/arduino-vertpantilt
class Driver(SMBusDriver):
    _CMD_MOVE = 0x4D
    _CMD_READ = 0x52


    def __init__(self, address, bus=1, movement=None, drivers=None,
        interval=0, read_interval=0, polling_interval=0.1, reset_pin=None):
        super().__init__(bus)
        self._address = address
        self._busnum = bus
        self._movement = movement
        self._drivers = drivers
        self._interval = interval
        self._read_interval = read_interval
        self._polling_interval = polling_interval
        self._reset_pin = reset_pin
        if self._reset_pin is not None:
            GPIO.setup(self._reset_pin, GPIO.IN)


    def run(self):
        sync_ns = int(self._interval * 1e9)
        try:
            for vert in _get_range(self._movement["vert"]):
                for pan in _get_range(self._movement["pan"]):
                    for tilt in _get_range(self._movement["tilt"]):
                        time.sleep(self._polling_interval)
                        self._move(vert, pan, tilt)
                        time.sleep(
                            self._polling_interval + self._read_interval)
                        # Drivers
                        if self._drivers:
                            self._bus.close()
                            if self._lock: self._lock.release()
                            yield from run_drivers(
                                self._drivers, self._interval)
                            if self._lock: self._lock.acquire()
                            self._bus = SMBus(self._busnum)
                        # Self
                        cvert, cpan, ctilt, cflags, cb1v, cb2v = self._read()
                        state = OrderedDict([
                            ("vert"     , cvert),
                            ("pan"      , cpan),
                            ("tilt"     , ctilt),
                            ("flags"    , cflags),
                            ("b1voltage", cb1v / 10),
                            ("b2voltage", cb2v / 10),
                        ])
                        ts = int(time.time() * 1e9)
                        yield self.sid(), round_step(ts, sync_ns), state
        except ResetError:
            self._move(0, 0, 0, False)
            time.sleep(3)
            while True:
                try:
                    self._read()
                    time.sleep(self._polling_interval)
                except ResetError:
                    time.sleep(3)
                    break


    def _move(self, vert, pan, tilt, check_reset=True):
        while True:
            try:
                self._send_move(vert, pan, tilt)
                time.sleep(self._polling_interval)
                cvert, cpan, ctilt, _, _, _ = self._send_read(check_reset)
                if cvert == vert and cpan == pan and ctilt == tilt:
                    return
                time.sleep(self._polling_interval)
            except OSError:
                time.sleep(self._polling_interval)


    def _read(self, check_reset=True):
        while True:
            try:
                return self._send_read(check_reset)
            except OSError:
                time.sleep(self._polling_interval)


    def _send_move(self, vert, pan, tilt):
        data = struct.pack(">HBB", vert, pan, tilt)
        checksum = (0xFF - (sum(data) & 0xFF) + 1) & 0xFF
        data += bytes([checksum])
        self._bus.write_i2c_block_data(self._address, self._CMD_MOVE, data)


    def _send_read(self, check_reset=True):
        if check_reset and self._reset_pin is not None \
           and not GPIO.input(self._reset_pin):
            raise ResetError()
        while True:
            data = bytes(self._bus.read_i2c_block_data(
                self._address, self._CMD_READ, 8))
            if sum(data) & 0xFF == 0:
                return struct.unpack(">HBBBBBB", data)[:-1]
            time.sleep(self._polling_interval)


def _get_range(cfg):
    return range(cfg["start"], cfg["stop"] + 1, cfg["step"])


class ResetError(Exception):
    pass