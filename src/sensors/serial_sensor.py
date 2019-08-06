from serial import Serial


class SerialReader:
    def __init__(self, *args, **kwargs):
        self._serial = Serial(*args, **kwargs)
        self._serial.flush()

    def __enter__(self):
        self._serial.__enter__(self)
    
    def __exit__(self, exc_type, exc_value, traceback):
        self._serial.__exit__(self, exc_type, exc_value, traceback)
