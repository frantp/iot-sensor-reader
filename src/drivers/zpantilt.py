from drivers.utils import SMBusDriver, run_drivers
import time
from collections import OrderedDict
from smbus2 import SMBus
import traceback


class Driver(SMBusDriver):
    _CMD_ZZZ = "V"
    _CMD_PAN = "P"
    _CMD_TLT = "T"
    _CMD_BT1 = "B1"
    _CMD_BT2 = "B2"
    _CMD_ZST = "VE"


    def __init__(self, address=0x16, movement=None, drivers=None,
        interval=0.1, check_move=True, common_timestamp=False):
        super().__init__()
        self._address = address
        self._movement = movement
        self._drivers = drivers
        self._interval = interval
        self._check_move = check_move
        self._common_timestamp = common_timestamp


    def run(self):
        self._reset()
        for z in _get_range(self._movement["z"]):
            self._move(self._CMD_ZZZ, z)
            for pan in _get_range(self._movement["pan"]):
                self._move(self._CMD_PAN, pan)
                for tilt in _get_range(self._movement["tilt"]):
                    self._move(self._CMD_TLT, tilt)
                    res_zzz = self._read_state(self._CMD_ZZZ)
                    res_pan = self._read_state(self._CMD_PAN)
                    res_tlt = self._read_state(self._CMD_TLT)
                    res_bt1 = self._read_state(self._CMD_BT1)
                    res_bt2 = self._read_state(self._CMD_BT2)
                    res_zst = self._read_state(self._CMD_ZST)
                    state = OrderedDict([
                        ("z"             , res_zzz),
                        ("pan"           , res_pan),
                        ("tilt"          , res_tlt),
                        ("battery1"      , res_bt1 & 0x3F),
                        ("battery2"      , res_bt2 & 0x3F),
                        ("battery1_state", (res_bt1 & 0xC0) >> 6),
                        ("battery2_state", (res_bt2 & 0xC0) >> 6),
                        ("z_state"       , res_zst),
                    ])
                    yield self.sid(), int(time.time() * 1e9), state
                    if self._drivers:
                        self._bus.close()
                        if self._lock: self._lock.release()
                        yield from run_drivers(
                            self._drivers, self._common_timestamp)
                        if self._lock: self._lock.acquire()
                        self._bus = SMBus(1)


    def _reset(self):
        self._move(self._CMD_TLT, 0)
        self._move(self._CMD_PAN, 0)
        self._move(self._CMD_ZZZ, 0)


    def _move(self, cmdid, value, force_check=False):
        cmd = "M{}{:03d}$".format(cmdid, value)
        _retry(lambda: self._bus.write_i2c_block_data(self._address,
            ord("@"), cmd.encode("ascii")), 0.5)
        if force_check or self._check_move:
            while True:
                time.sleep(self._interval)
                res = self._read_state(cmdid)
                if (cmdid == self._CMD_ZZZ and _close(res, value, 1)) or \
                   (cmdid == self._CMD_PAN and _close(res, value, 1)) or \
                   (cmdid == self._CMD_TLT and _close(res, value, 1)):
                    break
        else:
            time.sleep(self._interval)
            if cmdid == self._CMD_ZZZ:
                time.sleep(self._interval * 3)
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
            traceback.print_exc()
            time.sleep(interval)


def _get_range(cfg):
    return range(cfg["start"], cfg["stop"] + 1, cfg["step"])


def _close(a, b, tolerance):
    return abs(a - b) <= tolerance
