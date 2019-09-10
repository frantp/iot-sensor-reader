import os
from filelock import FileLock
import RPi.GPIO as GPIO
from serial import Serial
import time


def get_lock(lock_file):
    os.makedirs(os.path.dirname(lock_file), exist_ok=True)
    if not os.path.isfile(lock_file):
        os.mknod(lock_file)
    return FileLock(lock_file)


class ActivationContext:
    def __init__(self, pin=None):
        self._pin = pin
        self._open = False
        self._lock = get_lock("/run/lock/sreader/gpio.lock")


    def open(self):
        if not self._pin or self._open:
            return
        self._lock.acquire()
        GPIO.output(self._pin, GPIO.LOW)
        self._open = True


    def close(self):
        if not self._pin or not self._open:
            return
        self._open = False
        GPIO.output(self._pin, GPIO.HIGH)
        self._lock.release()


    def __enter__(self):
        self.open()
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class DriverBase:
    def __init__(self, lock_file=None):
        self._lock = get_lock(lock_file) if lock_file else None
        if self._lock:
            self._lock.acquire()


    def close(self):
        if self._lock:
            self._lock.release()


    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        if self._lock:
            self._lock.release()


class I2CDriver(DriverBase):
    def __init__(self):
        super().__init__("/run/lock/sreader/i2c.lock")


class SerialDriver(DriverBase):
    def __init__(self, *args, **kwargs):
        super().__init__("/run/lock/sreader/serial.lock")
        self._serial = Serial(timeout=1, *args, **kwargs)
        self._serial.reset_input_buffer()
        self._serial.reset_output_buffer()


    def close(self):
        self._serial.close()
        super().close()


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
