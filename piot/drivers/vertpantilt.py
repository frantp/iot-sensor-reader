from collections import OrderedDict
import struct
import sys
import time

from ..core import SMBusDriver, run_drivers
from smbus2 import SMBus


class Driver(SMBusDriver):
    _CMD_MOVE = 0x4D
    _CMD_READ = 0x52


    def __init__(self, address, bus=1, movement=None, drivers=None,
        interval=0, polling_interval=0.1, retry_interval=0.5, check_move=True):
        super().__init__(bus)
        self._address = address
        self._busnum = bus
        self._movement = movement
        self._drivers = drivers
        self._interval = interval
        self._polling_interval = polling_interval
        self._retry_interval = retry_interval
        self._check_move = check_move


    def run(self):
        for vert in _get_range(self._movement["vert"]):
            for pan in _get_range(self._movement["pan"]):
                for tilt in _get_range(self._movement["tilt"]):
                    self._move(vert, pan, tilt)
                    vert, pan, tilt, flags, bt1, bt2 = self._read()
                    state = OrderedDict([
                        ("vert"    , vert),
                        ("pan"     , pan),
                        ("tilt"    , tilt),
                        ("flags"   , flags),
                        ("battery1", bt1),
                        ("battery2", bt2),
                    ])
                    yield self.sid(), int(time.time() * 1e9), state
                    if self._drivers:
                        self._bus.close()
                        if self._lock: self._lock.release()
                        yield from run_drivers(self._drivers, self._interval)
                        if self._lock: self._lock.acquire()
                        self._bus = SMBus(self._busnum)


    def _move(self, vert, pan, tilt):
        data = struct.pack(">HBB", vert, pan, tilt)
        _retry(lambda:
            self._bus.write_i2c_block_data(self._address, self._CMD_MOVE, data),
            self._retry_interval)
        if self._check_move:
            while True:
                time.sleep(self._polling_interval)
                cvert, cpan, ctilt, _, _, _ = self._read()
                if cvert == vert and cpan == pan and ctilt == tilt:
                    break
        else:
            time.sleep(self._polling_interval)


    def _read(self):
        data = _retry(lambda:
            self._bus.read_i2c_block_data(self._address, self._CMD_READ, 7),
            self._retry_interval)
        return struct.unpack(">HBBBBB", bytes(data))


def _get_range(cfg):
    return range(cfg["start"], cfg["stop"] + 1, cfg["step"])


def _retry(func, interval):
    while True:
        try:
            return func()
        except OSError:
            print("[vertpantilt] OSError", file=sys.stderr)
            time.sleep(interval)
