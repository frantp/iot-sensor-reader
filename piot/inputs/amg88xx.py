from collections import OrderedDict
import time

from ..core import DriverBase
import board
import busio
from adafruit_amg88xx import AMG88XX


class Driver(DriverBase):
    def __init__(self, address=0x69):
        super().__init__()
        i2c = busio.I2C(board.SCL, board.SDA)
        self._sensor = AMG88XX(i2c, addr=address)

    def run(self):
        ts, temp, px = time.time_ns(), \
            self._sensor.temperature, self._sensor.pixels
        data = OrderedDict()
        data["temperature"] = temp
        for j, row in enumerate(px):
            for i, val in enumerate(row):
                data["px{}{}".format(i, j)] = val
        return [(self.sid(), ts, data)]
