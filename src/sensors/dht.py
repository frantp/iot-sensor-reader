import time
from collections import OrderedDict
from adafruit_dht import DHT11, DHT22


class Reader:
    def __init__(self, pin, dht11):
        self._sensor = DHT11(pin) if dht11 else DHT22(pin)

    def read(self):
        return int(time.time() * 1e9), OrderedDict([
            ("temperature", self._sensor.temperature),
            ("humidity",    self._sensor.humidity)
        ])
