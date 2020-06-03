from collections import OrderedDict
import time

from ..core import DriverBase
import board
import busio
from adafruit_ads1x15.ads1015 import ADS1015
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.ads1x15 import Mode
from adafruit_ads1x15.analog_in import AnalogIn


class Driver(DriverBase):
    _FACTOR = 0.00385

    def __init__(self, ads1015, positive_pin, negative_pin, r1, r2, vi=3.3,
                 gain=1, data_rate=None, mode=Mode.SINGLE, address=0x48):
        super().__init__()
        i2c = busio.I2C(board.SCL, board.SDA)
        ads = ADS1015(i2c, gain, data_rate, mode, address) \
            if ads1015 else ADS1115(i2c, gain, data_rate, mode, address)
        self._sensor = AnalogIn(ads, positive_pin, negative_pin)
        self._a = 1 / vi
        self._b = r1 / (r1 + r2)
        self._c = r2

    def run(self):
        value, vx = self._sensor.value, self._sensor.voltage
        val = self._a * vx + self._b
        rx = self._c * val / (1 - val)
        t = (rx / 100 - 1) / self._FACTOR
        return [(self.sid(), time.time_ns(), OrderedDict([
            ("value", value),
            ("voltage", vx),
            ("temperature", t),
        ]))]
