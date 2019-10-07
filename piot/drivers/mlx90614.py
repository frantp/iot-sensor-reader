from collections import OrderedDict
import time

from ..core import I2CDriver
import board
import busio
from adafruit_mlx90614 import MLX90614


class Driver(I2CDriver):
    def __init__(self, address=0x5a):
        super().__init__()
        i2c = busio.I2C(board.SCL, board.SDA)
        self._sensor = MLX90614(i2c, address=address)


    def run(self):
        return [(self.sid(), int(time.time() * 1e9), OrderedDict([
            ("ambient_temperature", self._sensor.ambient_temperature),
            ("object_temperature", self._sensor.object_temperature),
        ]))]
