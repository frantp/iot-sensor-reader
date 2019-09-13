from drivers.utils import DriverBase
import time
from collections import OrderedDict
from adafruit_hcsr04 import HCSR04


class Driver(DriverBase):
    def __init__(self, trigger_pin, echo_pin):
        super().__init__()
        self._sensor = HCSR04(trigger_pin, echo_pin)


    def run(self):
        return [(int(time.time() * 1e9), OrderedDict([
            ("distance", self._sensor.distance),
        ]))]


    def close(self):
        self._sensor.deinit()
        super().close()


    def __enter__(self):
        super().__enter__()
        self._sensor.__enter__()
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        self.close()