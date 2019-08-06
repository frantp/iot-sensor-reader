import time
from collections import OrderedDict
import board
import busio
from adafruit_bme680 import Adafruit_BME680_I2C


class Reader():
    def __init__(self, address=0x77, debug=False, refresh_rate=10):
        i2c = busio.I2C(board.SCL, board.SDA)
        self._sensor = Adafruit_BME680_I2C(i2c, address=address,
            debug=debug, refresh_rate=refresh_rate)

    def read(self):
        return time.time_ns(), OrderedDict([
            ("temperature", self._sensor.temperature),
            ("gas",         self._sensor.gas),
            ("humidity",    self._sensor.humidity),
            ("pressure",    self._sensor.pressure)
        ])
