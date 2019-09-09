from sensors.base.serial_sensor import SerialReader
import time
from collections import OrderedDict
from serial import SerialException


_REQUEST_SEQ = b"\xFF\x01\x86\x00\x00\x00\x00\x00\x79"
_CALZERO_SEQ = b"\xFF\x01\x87\x00\x00\x00\x00\x00\x78"
_CALSPAN_SEQ = b"\xFF\x01\x88\x07\xD0\x00\x00\x00\xA0"


def _checksum(res):
    return 0xFF - (sum(res[1:]) & 0xFF) + 1


def _check(res):
    return _checksum(res[:-1]) != res[-1]


class Reader(SerialReader):
    def __init__(self, port):
        super().__init__(port, 9600)

    def read(self):
        tm = int(time.time() * 1e9)
        self._serial.write(_REQUEST_SEQ)
        res = self._serial.read(9)
        if res[0:2] != b"\xFF\x86" or _check(res):
            raise SerialException("Incorrect response: {}".format(res.hex()))
        return tm, OrderedDict([
            ("co2", (res[2] << 8) + res[3]),
        ])
