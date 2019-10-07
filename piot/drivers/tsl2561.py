from collections import OrderedDict
import time

from ..core import I2CDriver
import board
import busio
from adafruit_tsl2561 import TSL2561


class Driver(I2CDriver):
    def __init__(self, address=0x39, gain=None, integration_time=None):
        super().__init__()
        i2c = busio.I2C(board.SCL, board.SDA)
        self._sensor = TSL2561(i2c, address)
        if gain:
            self._sensor.gain = gain
        if integration_time:
            self._sensor.integration_time = integration_time


    def run(self):
        return [(self.sid(), int(time.time() * 1e9), OrderedDict([
            ("lux", self._sensor.lux),
            ("broadband", self._sensor.broadband),
            ("infrared", self._sensor.infrared),
        ]))]
