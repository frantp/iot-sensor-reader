class ActivationContext:
    def __init__(self, pin=None):
        self._pin = pin
        self._open = False


    def open(self):
        if self._open:
            return
        GPIO.output(self._pin, GPIO.LOW)
        self._open = True


    def close(self):
        if not self._open:
            return
        self._open = False
        GPIO.output(self._pin, GPIO.HIGH)


    def __enter__(self):
        self.open()
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
