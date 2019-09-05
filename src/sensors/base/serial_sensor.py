from sensors.base.base_sensor import BaseReader
from serial import Serial


class SerialReader(BaseReader):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._serial = Serial(*args, **kwargs)
        self._serial.flush()

    def __enter__(self):
        super().__enter__()
        self._serial.__enter__(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._serial.__exit__(self, exc_type, exc_value, traceback)
        super().__exit__()
