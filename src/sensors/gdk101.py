from sensors.base.base_sensor import BaseReader
import time
from collections import OrderedDict
from smbus2 import SMBus


_CMD_RESET                    = 0xA0
_CMD_READ_STATUS              = 0xB0
_CMD_READ_MEASUREMENT_TIME    = 0xB1
_CMD_READ_MEASURING_VALUE_10M = 0xB2
_CMD_READ_MEASURING_VALUE_1M  = 0xB3
_CMD_READ_FIRMWARE_VERSION    = 0xB4


class Reader(BaseReader):
    def __init__(self, address=0x18):
        super().__init__()
        self._sensor = SMBus(1)
        self._address = address

    def read(self):
        tm = int(time.time() * 1e9)
        status, vibration = self._sensor.read_i2c_block_data(
            self._address, _CMD_READ_STATUS, 2)
        minutes, seconds = self._sensor.read_i2c_block_data(
            self._address, _CMD_READ_MEASUREMENT_TIME, 2)
        gint10m, gdec10m = self._sensor.read_i2c_block_data(
            self._address, _CMD_READ_MEASURING_VALUE_10M, 2)
        gint1m, gdec1m = self._sensor.read_i2c_block_data(
            self._address, _CMD_READ_MEASURING_VALUE_1M, 2)
        firmm, firms = self._sensor.read_i2c_block_data(
            self._address, _CMD_READ_FIRMWARE_VERSION, 2)
        return tm, OrderedDict([
            ("status", status),
            ("vibration", vibration),
            ("meastime", 60 * minutes + seconds),
            ("gamma10", gint10m + gdec10m / 100),
            ("gamma1", gint1m + gdec1m / 100),
            ("firmware", "{}.{}".format(firmm, firms)),
        ])
