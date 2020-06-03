from collections import OrderedDict
import contextlib
import struct
import sys
import time

from ..core import SMBusDriver, get_inputs, collect, round_step
from smbus2 import SMBus

import RPi.GPIO as GPIO


# Designed to work with arduino-vertpantilt:
# https://github.com/frantp/vertpantilt
class Driver(SMBusDriver):
    _CMD_MOVE = 0x4D
    _CMD_READ = 0x52

    def __init__(self, address, bus=1, movement=None, inputs=None,
                 interval=0, read_interval=0, vert_interval=0,
                 polling_interval=0.1, reset_pin=None):
        super().__init__(bus)
        self._address = address
        self._busnum = bus
        self._movement = movement
        self._inputs_cfg = inputs
        self._interval = interval
        self._read_interval = read_interval
        self._vert_interval = vert_interval
        self._polling_interval = polling_interval
        self._reset_pin = reset_pin
        if self._reset_pin is not None:
            GPIO.setup(self._reset_pin, GPIO.IN)

    def run(self):
        sync_ns = int(self._interval * 1e9)
        with contextlib.ExitStack() as stack:
            inputs = get_inputs(self._inputs_cfg, stack)
            try:
                for vert in _get_range(self._movement["vert"]):
                    first = True
                    for pan in _get_range(self._movement["pan"]):
                        for tilt in _get_range(self._movement["tilt"]):
                            time.sleep(self._polling_interval)
                            self._move(vert, pan, tilt)
                            if first:
                                first = False
                                time.sleep(self._vert_interval)
                            time.sleep(
                                self._polling_interval + self._read_interval)
                            # Inputs
                            if inputs:
                                self._bus.close()
                                yield from collect(inputs, self._interval)
                                self._bus = SMBus(self._busnum)
                            # Self
                            v, p, t, flags, b1v, b2v = self._read()
                            state = OrderedDict([
                                ("vert"     , v),
                                ("pan"      , p),
                                ("tilt"     , t),
                                ("flags"    , flags),
                                ("b1voltage", b1v / 10),
                                ("b2voltage", b2v / 10),
                            ])
                            ts = time.time_ns()
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
