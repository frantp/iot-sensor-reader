from collections import OrderedDict
import struct
import time

from ..core import SMBusDriver


_REG_WHO_AM_I   = 0x00
_REG_SMPLRT_DIV = 0x15
_REG_DLPF_FS    = 0x16
_REG_INT_CFG    = 0x17
_REG_INT_STATUS = 0x1A
_REG_DATA       = 0x1B
_REG_PWR_MGM    = 0x3E


class Driver(SMBusDriver):
    def __init__(self, address=0x68, bus=1):
        super().__init__(bus)
        self._address = address


    def run(self):
        ts = int(time.time() * 1e9)
        res = self._bus.read_i2c_block_data(self._address, _REG_DATA, 8)
        temperature, x, y, z = struct.unpack(">hhhh", bytearray(res))
        return [(self.sid(), ts, OrderedDict([
            ("temperature", temperature),
            ("gyro_x", x),
            ("gyro_y", y),
            ("gyro_z", z),
        ]))]
