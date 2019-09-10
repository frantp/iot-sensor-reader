from drivers.base import DriverBase
import time
from collections import OrderedDict
from adafruit_dht import DHT11, DHT22


class Driver(DriverBase):
    def __init__(self, pin, dht11):
        super().__init__()
        self._sensor = DHT11(pin) if dht11 else DHT22(pin)


    def run(self):
        return int(time.time() * 1e9), OrderedDict([
            ("temperature", self._sensor.temperature),
            ("humidity",    self._sensor.humidity)
        ])
