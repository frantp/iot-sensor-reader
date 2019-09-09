from drivers.base.base_driver import BaseDriver
import time
from collections import OrderedDict
import board
import busio
from adafruit_adxl34x import ADXL345


class Driver(BaseDriver):
    def __init__(self, address=0x53):
        i2c = busio.I2C(board.SCL, board.SDA)
        self._sensor = ADXL345(i2c, address=address)

    def run(self):
        tm, accel = int(time.time() * 1e9), self._sensor.acceleration
        return tm, OrderedDict([
            ("x", accel.x),
            ("y", accel.y),
            ("z", accel.z)
        ])