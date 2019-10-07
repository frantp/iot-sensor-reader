import time

from ..core import DriverBase


class Driver(DriverBase):
    def run(self):
        return [(self.sid(), int(time.time() * 1e9), None)]
