from drivers.base.base_driver import BaseDriver
from serial import Serial


class SerialDriver(BaseDriver):
    def __init__(self, *args, **kwargs):
        self._serial = Serial(*args, **kwargs)
        self._serial.flush()

    def __enter__(self):
        super().__enter__()
        self._serial.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._serial.__exit__(exc_type, exc_value, traceback)
        super().__exit__(exc_type, exc_value, traceback)
