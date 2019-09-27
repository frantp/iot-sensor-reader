from drivers.utils import DriverBase
import time
from collections import OrderedDict
import pypozyx


class Driver(DriverBase):
    def __init__(self, port=None):
        super().__init__()
        self._serial = pypozyx.PozyxSerial(
            port or pypozyx.get_first_pozyx_serial_port())

    def run(self):
        position = pypozyx.Coordinates()
        self._serial.doPositioning(position)
        return [(self.sid(), int(time.time() * 1e9), OrderedDict([
            ("pos_x", position.x),
            ("pos_y", position.y),
            ("pos_z", position.z),
        ]))]
