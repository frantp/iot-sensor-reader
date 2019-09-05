from sensors.base.base_sensor import BaseReader
import time
from collections import OrderedDict
import board
import busio
from adafruit_amg88xx import AMG88XX


class Reader(BaseReader):
    def __init__(self, address=0x69):
        super().__init__()
        i2c = busio.I2C(board.SCL, board.SDA)
        self._sensor = AMG88XX(i2c, addr=address)

    def read(self):
        tm, temp, px = int(time.time() * 1e9),
            self._sensor.temperature(), self._sensor.pixels()
        data = OrderedDict()
        data["temperature"] = temp
        for j, row in enumerate(pixels):
            for i, val in enumerate(row):
                pxd["px{}{}".format(i, j)] = val
        return tm, data
