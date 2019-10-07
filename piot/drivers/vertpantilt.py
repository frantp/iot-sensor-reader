from collections import OrderedDict
import sys
import time

from ..core import SMBusDriver, run_drivers
from smbus2 import SMBus


class Driver(SMBusDriver):
    _CMD_VRT = "V"
    _CMD_PAN = "P"
    _CMD_TLT = "T"
    _CMD_BT1 = "B1"
    _CMD_BT2 = "B2"
    _CMD_VST = "VE"


    def __init__(self, address, bus=1, movement=None, drivers=None,
        interval=0, polling_interval=0.1, check_move=True):
        super().__init__(bus)
        self._address = address
        self._busnum = bus
        self._movement = movement
        self._drivers = drivers
        self._interval = interval
        self._polling_interval = polling_interval
        self._check_move = check_move


    def run(self):
        self._reset()
        for vert in _get_range(self._movement["vert"]):
            self._move(self._CMD_VRT, vert)
            for pan in _get_range(self._movement["pan"]):
                self._move(self._CMD_PAN, pan)
                for tilt in _get_range(self._movement["tilt"]):
                    self._move(self._CMD_TLT, tilt)
                    res_vrt = self._read_state(self._CMD_VRT)
                    res_pan = self._read_state(self._CMD_PAN)
                    res_tlt = self._read_state(self._CMD_TLT)
                    res_vst = self._read_state(self._CMD_VST)
                    res_bt1 = self._read_state(self._CMD_BT1)
                    res_bt2 = self._read_state(self._CMD_BT2)
                    state = OrderedDict([
                        ("vert"         , res_vrt),
                        ("pan"          , res_pan),
                        ("tilt"         , res_tlt),
                        ("bat1_voltage" , res_bt1 & 0x3F),
                        ("bat2_voltage" , res_bt2 & 0x3F),
                        ("bat1_state"   , (res_bt1 & 0xC0) >> 6),
                        ("bat2_state"   , (res_bt2 & 0xC0) >> 6),
                        ("vert_state"   , res_vst),
                    ])
                    yield self.sid(), int(time.time() * 1e9), state
                    if self._drivers:
                        self._bus.close()
                        if self._lock: self._lock.release()
                        yield from run_drivers(self._drivers, self._interval)
                        if self._lock: self._lock.acquire()
                        self._bus = SMBus(self._busnum)


    def _reset(self):
        self._move(self._CMD_TLT, 0)
        self._move(self._CMD_PAN, 0)
        self._move(self._CMD_VRT, 0)


    def _move(self, cmdid, value, force_check=False):
        cmd = "M{}{:03d}$".format(cmdid, value)
        _retry(lambda: self._bus.write_i2c_block_data(self._address,
            ord("@"), cmd.encode("ascii")), 0.5)
        if force_check or self._check_move:
            while True:
                time.sleep(self._polling_interval)
                res = self._read_state(cmdid)
                if (cmdid == self._CMD_VRT and _close(res, value, 1)) or \
                   (cmdid == self._CMD_PAN and _close(res, value, 1)) or \
                   (cmdid == self._CMD_TLT and _close(res, value, 1)):
                    break
        else:
            time.sleep(self._polling_interval)
            if cmdid == self._CMD_VRT:
                time.sleep(self._polling_interval * 3)
        time.sleep(0.1)


    def _read_state(self, cmdid):
        cmd = "S{:<02}$".format(cmdid)
        _retry(lambda: self._bus.write_i2c_block_data(self._address,
            ord("@"), cmd.encode("ascii")), 0.5)
        time.sleep(0.1)
        _retry(lambda: self._bus.write_i2c_block_data(self._address,
            ord("@"), cmd.encode("ascii")), 0.5)
        return _retry(lambda: int(self._bus.read_byte(self._address)), 0.5)


def _retry(func, interval):
    while True:
        try:
            return func()
        except OSError:
            print("[vertpantilt] OSError", file=sys.stderr)
            time.sleep(interval)


def _get_range(cfg):
    return range(cfg["start"], cfg["stop"] + 1, cfg["step"])


def _close(a, b, tolerance):
    return abs(a - b) <= tolerance
