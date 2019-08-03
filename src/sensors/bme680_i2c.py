import time
import board
import busio
import adafruit_bme680

class Reader():
    def __init__(self, address=0x77, debug=False, refresh_rate=10):
        i2c = busio.I2C(board.SCL, board.SDA)
        self._sensor = adafruit_bme680.Adafruit_BME680_I2C(i2c,
            address=address, debug=debug, refresh_rate=refresh_rate)

    def read(self):
        return time.time_ns(), {
            "temperature": self._sensor.temperature,
            "gas":         self._sensor.gas,
            "humidity":    self._sensor.humidity,
            "pressure":    self._sensor.pressure,
            "altitude":    self._sensor.altitude,
        }
