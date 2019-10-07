from collections import OrderedDict
import time

from ..core import I2CDriver
import board
import busio
from adafruit_bme680 import Adafruit_BME680_I2C


class Driver(I2CDriver):
    def __init__(self, address=0x77, debug=False, refresh_rate=10):
        super().__init__()
        i2c = busio.I2C(board.SCL, board.SDA)
        self._sensor = Adafruit_BME680_I2C(i2c, address=address,
            debug=debug, refresh_rate=refresh_rate)


    def run(self):
        return [(self.sid(), int(time.time() * 1e9), OrderedDict([
            ("temperature", self._sensor.temperature),
            ("gas",         self._sensor.gas),
            ("humidity",    self._sensor.humidity),
            ("pressure",    self._sensor.pressure),
        ]))]
