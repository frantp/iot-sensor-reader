import time
from collections import OrderedDict
from serial_sensor import SerialReader
from serial import SerialException
import struct


_PASSIVE_CODES = b"\x02\x01\x01"
_REQUEST_CODES = b"\x04\x00\x00"
_SETWORK_CODES = b"\x06\x01\x01"
_SETCONT_CODES = b"\x08\x01\x00"


def _seq(codes, device_id=b"\xFF\xFF"):
    head = b"\xAA\xB4" + codes + b"\x00" * 10 + device_id
    return head + bytes([_checksum(head)]) + b"\xAB"


def _checksum(res):
    return sum(res[2:]) & 0xFF


class Reader(SerialReader):
    def __init__(self, port):
        super().__init__(port, 9600)
        self._serial.write(_seq(_PASSIVE_CODES))
        res = self._serial.read(10)
        if res[0:2] != b"\xAA\xC5\x05" or _checksum(res[:-1]) != res[-1]:
            raise SerialException("Incorrect response")
        self._serial.write(_seq(_SETWORK_CODES))
        res = self._serial.read(10)
        if res[0:2] != b"\xAA\xC5\x06" or _checksum(res[:-1]) != res[-1]:
            raise SerialException("Incorrect response")
        self._serial.write(_seq(_SETCONT_CODES))
        res = self._serial.read(10)
        if res[0:2] != b"\xAA\xC5\x08" or _checksum(res[:-1]) != res[-1]:
            raise SerialException("Incorrect response")
        

    def read(self):
        tm = int(time.time() * 1e9)
        self._serial.write(_seq(_REQUEST_CODES))
        res = self._serial.read(10)
        if res[0:1] != b"\xAA\xC0" or _checksum(res[:-1]) != res[-1]:
            return tm, None
        pm25, pm10 = [x / 10 for x in struct.unpack("<HH", res[2:6])]
        return tm, OrderedDict([
            ("pm25", pm25),
            ("pm10", pm10)
        ])
