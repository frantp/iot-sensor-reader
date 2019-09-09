from drivers.base.base_driver import BaseDriver
import time
from collections import OrderedDict
import board
import busio
from adafruit_bme280 import Adafruit_BME280_I2C


class Driver(BaseDriver):
    def __init__(self, address=0x77):
        i2c = busio.I2C(board.SCL, board.SDA)
        self._sensor = Adafruit_BME280_I2C(i2c, address=address)

    def run(self):
        return int(time.time() * 1e9), OrderedDict([
            ("temperature", self._sensor.temperature),
            ("gas",         self._sensor.gas),
            ("humidity",    self._sensor.humidity),
            ("pressure",    self._sensor.pressure)
        ])