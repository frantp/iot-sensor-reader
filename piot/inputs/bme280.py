from collections import OrderedDict
import time

from ..core import DriverBase
import board
import busio
from adafruit_bme280 import Adafruit_BME280_I2C


class Driver(DriverBase):
    def __init__(self, address=0x77):
        super().__init__()
        i2c = busio.I2C(board.SCL, board.SDA)
        self._sensor = Adafruit_BME280_I2C(i2c, address=address)

    def run(self):
        return [(self.sid(), time.time_ns(), OrderedDict([
            ("temperature", self._sensor.temperature),
            ("humidity",    self._sensor.humidity),
            ("pressure",    self._sensor.pressure),
        ]))]
