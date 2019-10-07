from collections import OrderedDict
import struct
import time

from ..core import SerialDriver
from serial import SerialException


def _checksum(res):
    return sum(res) & 0xFF


def _check(res):
    return _checksum(res[:-1]) != res[-1]


class Driver(SerialDriver):
    def __init__(self, port):
        super().__init__(port, 115200)


    def run(self):
        ts = int(time.time() * 1e9)
        self._serial.read_until(b"\x59\x59")
        res = b"\x59\x59" + self._serial.read(7)
        if _check(res):
            raise SerialException("Incorrect response: {}".format(res.hex()))
        distance, strength = struct.unpack("<HH", res[2:6])
        return [(self.sid(), ts, OrderedDict([
            ("distance", distance),
            ("strength", strength),
        ]))]
