from collections import OrderedDict
import struct
import time

from ..core import SerialDriver
from serial import SerialException


_PASSIVE_CODES = b"\x02\x01\x01"
_REQUEST_CODES = b"\x04\x00\x00"
_SETWORK_CODES = b"\x06\x01\x01"
_SETCONT_CODES = b"\x08\x01\x00"


def _seq(codes, device_id=b"\xFF\xFF"):
    head = b"\xAA\xB4" + codes + b"\x00" * 10 + device_id
    return head + bytes([_checksum(head)]) + b"\xAB"


def _checksum(res):
    return sum(res[2:]) & 0xFF


def _check(res):
    return res[-1:] != b"\xAB" or _checksum(res[:-2]) != res[-2]


class Driver(SerialDriver):
    def __init__(self, port):
        super().__init__(port, 9600)
        res = self._cmd(_seq(_PASSIVE_CODES), 10)
        if res[0:3] != b"\xAA\xC5\x02" or _check(res):
            raise SerialException("Incorrect response: {}".format(res.hex()))
        res = self._cmd(_seq(_SETWORK_CODES), 10)
        if res[0:3] != b"\xAA\xC5\x06" or _check(res):
            raise SerialException("Incorrect response: {}".format(res.hex()))
        res = self._cmd(_seq(_SETCONT_CODES), 10)
        if res[0:3] != b"\xAA\xC5\x08" or _check(res):
            raise SerialException("Incorrect response: {}".format(res.hex()))
        

    def run(self):
        ts = int(time.time() * 1e9)
        res = self._cmd(_seq(_REQUEST_CODES), 10)
        if res[0:2] != b"\xAA\xC0" or _check(res):
            return ts, None
        pm25, pm10 = [x / 10 for x in struct.unpack("<HH", res[2:6])]
        return [(self.sid(), ts, OrderedDict([
            ("pm25", pm25),
            ("pm10", pm10),
        ]))]
