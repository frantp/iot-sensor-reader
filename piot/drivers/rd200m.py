from collections import OrderedDict
import time

from ..core import SerialDriver
from serial import SerialException


_REQUEST_SEQ = b"\x02\x01\x00\xFE"


def _checksum(res):
    return 0xFF - (sum(res[1:]) & 0xFF)


def _check(res):
    return _checksum(res[:-1]) != res[-1]


class Driver(SerialDriver):
    def __init__(self, port):
        super().__init__(port, 19200)


    def run(self):
        ts = int(time.time() * 1e9)
        res = self._cmd(_REQUEST_SEQ, 8)
        if res[0:3] != b"\x02\x10\x04" or _check(res):
            raise SerialException("Incorrect response: {}".format(res.hex()))
        status, minutes, rint, rdec = res[3:7]
        return [(self.sid(), ts, OrderedDict([
            ("status", status),
            ("meastime", 60 * minutes),
            ("radon", (rint + rdec / 100) * 37),  # pCi/L -> Bq/m^3
        ]))]
