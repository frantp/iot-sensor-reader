from sensors.base.base_sensor import BaseReader
import time
from collections import OrderedDict
import board
import busio
from adafruit_adxl34x import ADXL345


class Reader(BaseReader):
    def __init__(self, address=0x53):
        super().__init__()
        i2c = busio.I2C(board.SCL, board.SDA)
        self._sensor = ADXL345(i2c, address=address)

    def read(self):
        tm, accel = int(time.time() * 1e9), self._sensor.acceleration
        return tm, OrderedDict([
            ("x", accel.x),
            ("y", accel.y),
            ("z", accel.z)
        ])
