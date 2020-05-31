import os

from ..core import DriverBase, format_msg


class Driver(DriverBase):
    def __init__(self, file="/dev/stdout"):
        super().__init__()
        self._fd = open(file, "a")

    def close(self):
        self._fd.close()
        super().close()

    def run(self, driver_id, ts, fields, tags):
        if not fields:
            return
        msg = format_msg(ts, driver_id, tags, fields)
        self._fd.write(msg + os.linesep)
