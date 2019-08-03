import time
import board
import busio
import adafruit_bme280

class Reader():
    def __init__(self, address=adafruit_bme280._BME280_ADDRESS):
        i2c = busio.I2C(board.SCL, board.SDA)
        self._sensor = adafruit_bme280.Adafruit_BME280_I2C(i2c,
            address=address)

    def read(self):
        return time.time_ns(), {
            "temperature": self._sensor.temperature,
            "gas":         self._sensor.gas,
            "humidity":    self._sensor.humidity,
            "pressure":    self._sensor.pressure,
            "altitude":    self._sensor.altitude,
        }
