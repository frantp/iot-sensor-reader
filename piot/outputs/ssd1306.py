import datetime
import os
import socket
import subprocess

from ..core import DriverBase, TAG_ERROR, ERROR_NOLIB, ERROR_EXCEP
import board
import busio
from adafruit_ssd1306 import SSD1306_I2C


class Driver(DriverBase):
    _OK = 0
    _NOLIB = 1
    _EXCEP = 2

    def __init__(self, width, height, addr=0x3C, reset=None):
        super().__init__()
        i2c = busio.I2C(board.SCL, board.SDA)
        self._disp = SSD1306_I2C(width, height, i2c, addr=addr, reset=reset)
        self._buffer = {}

    def run(self, driver_id, ts, fields, tags):
        if not fields:
            if TAG_ERROR in tags:
                if tags[TAG_ERROR] == ERROR_NOLIB:
                    self._buffer[driver_id] = self._NOLIB
                elif tags[TAG_ERROR] == ERROR_EXCEP:
                    self._buffer[driver_id] = self._EXCEP
            else:
                return
        else:
            self._buffer[driver_id] = self._OK

        # Retrieve values
        timestr = datetime.datetime.now().strftime("%m-%d %H:%M:%S")
        try:
            ssid = subprocess.check_output(["/sbin/iwgetid", "-r"]) \
                .decode("utf-8").strip()
        except Exception:
            ssid = "---"
        devid = socket.gethostname()
        devip = subprocess.check_output(["hostname", "-I"]) \
            .decode("utf-8").strip()

        # Show values
        font_name = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "font5x8.bin")
        cw = 21
        idcw = cw - len(devip)
        self._disp.fill(0)
        self._disp.text(f"{devid[:6]:<6}|{timestr}", 1, 0, 0xFF,
                        font_name=font_name)
        self._disp.text(f"{ssid[:idcw - 1] + ':':<{idcw}}{devip}", 0, 8, 0xFF,
                        font_name=font_name)
        for i, (did, state) in enumerate(self._buffer.items()):
            y = 16 + 8 * (i // 6)
            ix = i % 6
            self._disp.text(did[:3], 1 + 21 * ix, y, 0xFF,
                            font_name=font_name)
            ys = [5, 6, 7] if state == self._OK \
                else [5, 7] if state == self._EXCEP \
                else [7]
            for yi in ys:
                self._disp.pixel(19 + 21 * ix, y + yi, 0xFF)
        self._disp.show()
