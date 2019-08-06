import time
from collections import OrderedDict
from serial_sensor import SerialReader
from serial import SerialException


_REQUEST_SEQ = b"\x02\x01\x00\xFE"


def _checksum(res):
    return 0xFF - (sum(res[1:]) & 0xFF)


class Reader(SerialReader):
    def __init__(self, port):
        super().__init__(port, 19200)

    def read(self):
        tm = time.time_ns()
        self._serial.write(_REQUEST_SEQ)
        res = self._serial.read(8)
        if res[0:2] != b"\x02\x01\x04" or _checksum(res[:-1]) != res[-1]:
            raise SerialException("Incorrect response")
        status, minutes, rint, rdec = res[3:7]
        return tm, OrderedDict([
            ("status", status),
            ("meastime", 60 * minutes),
            ("radon", (rint + rdec / 100) * 37)  # pCi/L -> Bq/m^3
        ])
