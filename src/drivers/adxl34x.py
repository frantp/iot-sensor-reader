from drivers.utils import I2CDriver
import time
from collections import OrderedDict
import board
import busio
from adafruit_adxl34x import ADXL345


class Driver(I2CDriver):
    def __init__(self, address=0x53):
        super().__init__()
        i2c = busio.I2C(board.SCL, board.SDA)
        self._sensor = ADXL345(i2c, address=address)


    def run(self):
        ts, x, y, z = int(time.time() * 1e9), *self._sensor.acceleration
        return [(self.sid(), ts, OrderedDict([
            ("x", x),
            ("y", y),
            ("z", z),
        ]))]
