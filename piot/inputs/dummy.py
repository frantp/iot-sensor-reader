import time

from ..core import DriverBase


class Driver(DriverBase):
    def run(self):
        return [(self.sid(), time.time_ns(), None)]
