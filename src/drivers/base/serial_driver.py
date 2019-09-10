from drivers.base.base_driver import BaseDriver
from serial import Serial
import time


class SerialDriver(BaseDriver):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._serial = Serial(timeout=1, *args, **kwargs)
        self._serial.reset_input_buffer()
        self._serial.reset_output_buffer()

    def __enter__(self):
        super().__enter__()
        self._serial.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._serial.__exit__(exc_type, exc_value, traceback)
        super().__exit__(exc_type, exc_value, traceback)

    def _cmd(self, data, size=1):
        self._serial.write(data)
        self._serial.flush()
        time.sleep(0.1)
        return self._serial.read(size)
