from drivers.base.errors import ActivationError
import RPi.GPIO as GPIO

class BaseDriver:
    def __init__(self):
        self._activation_pin = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.deactivate()

    def activate(self, pin=None):
        if pin:
            if self._activation_pin:
                raise ActivationError("Already activated")
            self._activation_pin = pin
            GPIO.output(self._activation_pin, GPIO.LOW)
        return self

    def deactivate(self):
        if self._activation_pin:
            GPIO.output(self._activation_pin, GPIO.HIGH)
            self._activation_pin = None
