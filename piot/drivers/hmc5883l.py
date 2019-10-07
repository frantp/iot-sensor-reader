from collections import OrderedDict
import struct
import time

from ..core import SMBusDriver


_REG_CFGA = 0x00
_REG_CFGB = 0x01
_REG_MODE = 0x02
_REG_DATA = 0x03


class Driver(SMBusDriver):
    def __init__(self, address=0x1E, bus=1):
        super().__init__(bus)
        self._address = address
        self._bus.write_byte_data(self._address, _REG_MODE, 0x00)


    def run(self):
        ts = int(time.time() * 1e9)
        res = self._bus.read_i2c_block_data(self._address, _REG_DATA, 7)
        x, y, z, status = struct.unpack(">hhhB", bytearray(res))
        return [(self.sid(), ts, OrderedDict([
            ("mag_x", x),
            ("mag_y", y),
            ("mag_z", z),
            ("status", status),
        ]))]
