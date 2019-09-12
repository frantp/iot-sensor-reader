from drivers.utils import DriverBase
import time


class Driver(DriverBase):
    def run(self):
        return [(int(time.time() * 1e9), None)]
