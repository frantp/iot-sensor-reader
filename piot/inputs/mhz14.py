from collections import OrderedDict
import struct
import time

from ..core import SerialDriver
from serial import SerialException


_REQUEST_SEQ       = b"\xFF\x01\x86\x00\x00\x00\x00\x00\x79"
_CALZERO_SEQ       = b"\xFF\x01\x87\x00\x00\x00\x00\x00\x78"
_CALSPAN_SEQ       = b"\xFF\x01\x88\x07\xD0\x00\x00\x00\xA0"
_ABCENABLE_SEQ     = b"\xFF\x01\x79\xA0\x00\x00\x00\x00\xE6"
_ABCDISABLE_SEQ    = b"\xFF\x01\x79\x00\x00\x00\x00\x00\x86"
_RESET_SEQ         = b"\xFF\x01\x8d\x00\x00\x00\x00\x00\x72"
_MEASRANGE1000_SEQ = b"\xFF\x01\x99\x00\x00\x00\x03\xE8\x7B"
_MEASRANGE2000_SEQ = b"\xFF\x01\x99\x00\x00\x00\x07\xD0\x8F"
_MEASRANGE3000_SEQ = b"\xFF\x01\x99\x00\x00\x00\x0B\xB8\xA3"
_MEASRANGE5000_SEQ = b"\xFF\x01\x99\x00\x00\x00\x13\x88\xCB"


def _checksum(res):
    return (0xFF - (sum(res[1:]) & 0xFF) + 1) & 0xFF


def _check(res):
    return _checksum(res[:-1]) != res[-1]


class Driver(SerialDriver):
    zerocalibrated = False
    spancalibrated = False

    def __init__(self, port, zerocalibrate=False, spancalibrate=False,
                 autocalibrate=True):
        super().__init__(port, 9600)
        self.zerocalibrate = zerocalibrate
        self.spancalibrate = spancalibrate
        self.autocalibrate = autocalibrate

    def run(self):
        ts = time.time_ns()
        with self._open_serial() as serial:
            if self.zerocalibrate and not Driver.zerocalibrated:
                self._cmd(serial, _CALZERO_SEQ, 9)
                Driver.zerocalibrated = True
            if self.spancalibrate and not Driver.spancalibrated:
                self._cmd(serial, _CALZERO_SEQ, 9)
                Driver.spancalibrated = True
            if self.autocalibrate:
                self._cmd(serial, _ABCENABLE_SEQ, 9)
            else:
                self._cmd(serial, _ABCDISABLE_SEQ, 9)
            res = self._cmd(serial, _REQUEST_SEQ, 9)
        if res[0:2] != b"\xFF\x86" or _check(res):
            raise SerialException("Incorrect response: {}".format(res.hex()))
        co2, = struct.unpack(">H", res[2:4])
        return [(self.sid(), ts, OrderedDict([
            ("co2", co2),
        ]))]
