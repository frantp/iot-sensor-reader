import time
from collections import OrderedDict
import board
import busio
from adafruit_amg88xx import AMG88XX

class Reader():
    def __init__(self, address=0x69):
        i2c = busio.I2C(board.SCL, board.SDA)
        self._sensor = AMG88XX(i2c, addr=address)

    def read(self):
        tm, temp, px = time.time_ns(),
            self._sensor.temperature(), self._sensor.pixels()
        data = OrderedDict()
        data["temperature"] = temp
        for j, row in enumerate(pixels):
            for i, val in enumerate(row):
                pxd[f"px{i}{j}"] = val
        return tm, data
