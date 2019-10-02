from drivers.utils import DriverBase
import time
from collections import OrderedDict
import pypozyx


class Driver(DriverBase):
    def __init__(self, i2c=False, bus=1, port=None):
        super().__init__()
        self._sensor = pypozyx.PozyxI2C(bus) if i2c else \
            pypozyx.PozyxSerial(port or pypozyx.get_first_pozyx_serial_port())


    def run(self):
        position = pypozyx.Coordinates()
        while position.x == position.y == position.z == 0:
            self._sensor.doPositioning(position)
        return [(self.sid(), int(time.time() * 1e9), OrderedDict([
            ("pos_x", position.x),
            ("pos_y", position.y),
            ("pos_z", position.z),
        ]))]
