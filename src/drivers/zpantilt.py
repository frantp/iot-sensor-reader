from drivers.utils import I2CDriver, run_drivers
import time
from collections import OrderedDict
from smbus2 import SMBus


class Driver(I2CDriver):
    _CMD_ZZZ = "V"
    _CMD_PAN = "P"
    _CMD_TLT = "T"
    _CMD_BT1 = "B1"
    _CMD_BT2 = "B2"
    _CMD_ZST = "VE"


    def __init__(self, address=0x16, movement=None, drivers=None,
        polling_interval=1):
        super().__init__()
        self._address = address
        self._movement = movement
        self._drivers = drivers
        self._polling_interval = polling_interval


    def run(self):
        bus = SMBus(1)
        self._reset(bus)
        for z in _get_range(self._movement["z"]):
            self._move(bus, self._CMD_ZZZ, z)
            for pan in _get_range(self._movement["pan"]):
                self._move(bus, self._CMD_PAN, pan)
                for tilt in _get_range(self._movement["tilt"]):
                    self._move(bus, self._CMD_TLT, tilt)
                    if self._drivers:
                        res_zzz = self._read_state(bus, self._CMD_ZZZ)
                        res_pan = self._read_state(bus, self._CMD_PAN)
                        res_tlt = self._read_state(bus, self._CMD_TLT)
                        res_bt1 = self._read_state(bus, self._CMD_BT1)
                        res_bt2 = self._read_state(bus, self._CMD_BT2)
                        res_zst = self._read_state(bus, self._CMD_ZST)
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
                        yield from run_drivers(self._drivers)
        bus.close()


    def _move(self, bus, cmdid, value):
        cmd = "M{}{:03d}$".format(cmdid, value)
        bus.write_i2c_block_data(self._address, ord("@"), cmd.encode("ascii"))
        while True:
            time.sleep(self._polling_interval)
            res = self._read_state(bus, cmdid)
            if (cmdid == self._CMD_ZZZ and _close(res, value, 0)) or \
               (cmdid == self._CMD_PAN and _close(res, value, 1)) or \
               (cmdid == self._CMD_TLT and _close(res, value, 1)):
                break
        time.sleep(0.1)


    def _reset(self, bus):
        self._move(bus, self._CMD_TLT, 0)
        self._move(bus, self._CMD_PAN, 0)
        self._move(bus, self._CMD_ZZZ, 0)


    def _read_state(self, bus, cmdid):
        cmd = "S{:<02}$".format(cmdid)
        bus.write_i2c_block_data(self._address, ord("@"), cmd.encode("ascii"))
        time.sleep(0.1)
        return int(bus.read_byte(self._address))


def _get_range(cfg):
    return range(cfg["start"], cfg["stop"] + 1, cfg["step"])


def _close(a, b, tolerance):
    return abs(a - b) <= tolerance
