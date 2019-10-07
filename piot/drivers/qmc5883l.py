from collections import OrderedDict
import struct
import time

from ..core import SMBusDriver


_REG_DATA        = 0x00
_REG_STATUS      = 0x06
_REG_TEMPERATURE = 0x07
_REG_CTRL1       = 0x09
_REG_CTRL2       = 0x0A
_REG_PERIOD      = 0x0B


class Driver(SMBusDriver):
    def __init__(self, address=0x0D, bus=1):
        super().__init__(bus)
        self._address = address
        self._bus.write_byte_data(self._address, _REG_CTRL1, 0x01)


    def run(self):
        ts = int(time.time() * 1e9)
        res = self._bus.read_i2c_block_data(self._address, _REG_DATA, 9)
        x, y, z, status, temperature = struct.unpack("<hhhBh", bytearray(res))
        return [(self.sid(), ts, OrderedDict([
            ("mag_x", x),
            ("mag_y", y),
            ("mag_z", z),
            ("status", status),
            ("temperature", temperature),
        ]))]
