import time
from collections import OrderedDict
import board
import busio
from adafruit_tsl2591 import TSL2591


class Reader:
    def __init__(self, address=0x29, gain=None, integration_time=None):
        i2c = busio.I2C(board.SCL, board.SDA)
        self._sensor = TSL2591(i2c, address)
        if gain:
            self._sensor.gain = gain
        if integration_time:
            self._sensor.integration_time = integration_time

    def read(self):
        return int(time.time() * 1e9), OrderedDict([
            ("lux", self._sensor.lux),
            ("visible", self._sensor.visible),
            ("infrared", self._sensor.infrared)
        ])
