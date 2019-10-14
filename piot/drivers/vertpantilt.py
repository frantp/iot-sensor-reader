from collections import OrderedDict
import struct
import sys
import time

from ..core import SMBusDriver, run_drivers
from smbus2 import SMBus


# Designed to work with arduino-vertpantilt:
# https://github.com/frantp/arduino-vertpantilt
class Driver(SMBusDriver):
    _CMD_MOVE = 0x4D
    _CMD_READ = 0x52


    def __init__(self, address, bus=1, movement=None, drivers=None,
        interval=0, read_interval=0, polling_interval=0.1):
        super().__init__(bus)
        self._address = address
        self._busnum = bus
        self._movement = movement
        self._drivers = drivers
        self._interval = interval
        self._read_interval = read_interval
        self._polling_interval = polling_interval


    def run(self):
        for vert in _get_range(self._movement["vert"]):
            for pan in _get_range(self._movement["pan"]):
                for tilt in _get_range(self._movement["tilt"]):
                    time.sleep(self._polling_interval)
                    self._move(vert, pan, tilt)
                    time.sleep(self._polling_interval + self._read_interval)
                    cvert, cpan, ctilt, cflags, cbt1, cbt2 = self._read()
                    state = OrderedDict([
                        ("vert"    , cvert),
                        ("pan"     , cpan),
                        ("tilt"    , ctilt),
                        ("flags"   , cflags),
                        ("battery1", cbt1),
                        ("battery2", cbt2),
                    ])
                    yield self.sid(), int(time.time() * 1e9), state
                    if self._drivers:
                        self._bus.close()
                        if self._lock: self._lock.release()
                        yield from run_drivers(self._drivers, self._interval)
                        if self._lock: self._lock.acquire()
                        self._bus = SMBus(self._busnum)


    def _move(self, vert, pan, tilt):
        while True:
            try:
                self._send_move(vert, pan, tilt)
                time.sleep(self._polling_interval)
                cvert, cpan, ctilt, _, _, _ = self._send_read()
                if cvert == vert and cpan == pan and ctilt == tilt:
                    return
                time.sleep(self._polling_interval)
            except OSError:
                time.sleep(self._polling_interval)


    def _read(self):
        while True:
            try:
                return self._send_read()
            except OSError:
                time.sleep(self._polling_interval)


    def _send_move(self, vert, pan, tilt):
        data = struct.pack(">HBB", vert, pan, tilt)
        checksum = (0xFF - (sum(data) & 0xFF) + 1) & 0xFF
        data += bytes([checksum])
        self._bus.write_i2c_block_data(self._address, self._CMD_MOVE, data)


    def _send_read(self):
        while True:
            data = bytes(self._bus.read_i2c_block_data(
                self._address, self._CMD_READ, 8))
            if sum(data) & 0xFF == 0:
                return struct.unpack(">HBBBBBB", data)[:-1]
            time.sleep(self._polling_interval)


def _get_range(cfg):
    return range(cfg["start"], cfg["stop"] + 1, cfg["step"])
