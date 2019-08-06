import time
from collections import OrderedDict
import board
import busio
from adafruit_adxl34x import ADXL345


class Reader():
    def __init__(self, address=0x53):
        i2c = busio.I2C(board.SCL, board.SDA)
        self._sensor = ADXL345(i2c, address=address)

    def read(self):
        tm, accel = time.time_ns(), self._sensor.acceleration
        return tm, OrderedDict([
            ("x", accel.x),
            ("y", accel.y),
            ("z", accel.z)
        ])
