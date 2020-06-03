import datetime
import os
import socket
import subprocess

from ..core import DriverBase, TAG_ERROR
import board
import busio
from adafruit_ssd1306 import SSD1306_I2C


class Driver(DriverBase):

    def __init__(self, width, height, addr=0x3C, reset=None):
        super().__init__()
        i2c = busio.I2C(board.SCL, board.SDA)
        self._disp = SSD1306_I2C(width, height, i2c, addr=addr, reset=reset)
        self._buffer = {}

    def run(self, driver_id, ts, fields, tags):
        ltags = [v for k, v in tags.items() if k != TAG_ERROR]
        if not fields:
            if TAG_ERROR in tags:
                # Error
                self._buffer[(driver_id, *ltags)] = False
            else:
                # Sensor without output, discard
                return
        else:
            # Valid result
            self._buffer[(driver_id, *ltags)] = True

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
        for i, ((did, *_), ok) in enumerate(self._buffer.items()):
            y = 16 + 8 * (i // 6)
            ix = i % 6
            self._disp.text(did[:3], 1 + 21 * ix, y, 0xFF,
                            font_name=font_name)
            for yi in [5, 6, 7] if ok else [7]:
                self._disp.pixel(19 + 21 * ix, y + yi, 0xFF)
        self._disp.show()
