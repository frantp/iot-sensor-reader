from drivers.utils import SerialDriver
import time
from collections import OrderedDict
from serial import SerialException
import struct


def _checksum(res):
    return sum(res) & 0xFF


def _check(res):
    return _checksum(res[:-1]) != res[-1]


class Driver(SerialDriver):
    def __init__(self, port):
        super().__init__(port, 115200)


    def run(self):
        tm = int(time.time() * 1e9)
        res = self._serial.read(9)
        if res[0:2] != b"\x59\x59" or _check(res):
            raise SerialException("Incorrect response: {}".format(res.hex()))
        distance, strength = struct.unpack("<HH", res[2:6])
        return [(self.sid(), tm, OrderedDict([
            ("distance", distance),
            ("strength", strength),
        ]))]
