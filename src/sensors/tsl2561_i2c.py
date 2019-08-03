import time
import tsl2561

class Reader():
    def __init__(self, address=None, busnum=None,
        integration_time=tsl2561.TSL2561_INTEGRATIONTIME_402MS,
        gain=tsl2561.TSL2561_GAIN_1X, autogain=False, debug=False):
        self._sensor = tsl2561.TSL2561(address, busnum, integration_time,
            gain, autogain, debug)

    def read(self):
        return time.time_ns(), {
            "lux": self._sensor.lux()
        }
