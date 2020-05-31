#!/usr/bin/env python3

from collections import OrderedDict
import contextlib
from filelock import FileLock
import importlib
import os
from serial import Serial
from smbus2 import SMBus
import socket
import sys
import time
import toml
import traceback

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None


__all__ = [
    "collect", "GPIOContext", "ActivationContext",
    "DriverBase", "I2CDriver", "SMBusDriver", "SerialDriver"
]


TAG_ERROR = "ERROR"
ERROR_NOLIB = "NOLIB"
ERROR_EXCEP = "EXCEP"


ACT_PIN_ID = "ACTIVATION_PIN"
LOCK_PREFIX = "/run/lock/piot"


def get_lock(lock_file):
    os.makedirs(os.path.dirname(lock_file), exist_ok=True)
    if not os.path.isfile(lock_file):
        os.mknod(lock_file)
    return FileLock(lock_file)


def find(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            yield obj[key]
        for v in obj.values():
            yield from find(v, key)
    elif isinstance(obj, list):
        for v in obj:
            yield from find(v, key)


def format_msg(timestamp, measurement, tags, fields):
    tstr = ",".join(["{}={}".format(k, v) for k, v in tags.items()])
    fstr = ",".join(["{0}={3}{1}{2}{3}".format(
        k, v,
        "i" if isinstance(v, int) else "",
        "\"" if isinstance(v, str) else "")
        for k, v in fields.items()]
    )
    return "{},{} {} {}".format(measurement, tstr, fstr, timestamp)


def sync_wait(sync):
    return sync - time.time() % sync if sync > 0 else 0


def round_step(x, step):
    return x // step * step if step else x


def collect(cfg, sync=0):
    sync_ns = int(sync * 1e9)
    time.sleep(sync_wait(sync))
    for driver_id in cfg:
        for dcfg in cfg[driver_id]:
            try:
                activation_pin = None
                if ACT_PIN_ID in dcfg:
                    activation_pin = dcfg[ACT_PIN_ID]
                    dcfg = {k: v for k, v in dcfg.items() if k != ACT_PIN_ID}
                driver_module = importlib.import_module(
                    "piot.inputs." + driver_id)
                with ActivationContext(activation_pin), \
                        getattr(driver_module, "Driver")(**dcfg) as driver:
                    res = driver.run()
                    for did, ts, fields, *tags in res:
                        tags.extend([(driver_id + "." + k, v)
                                    for k, v in dcfg.items()
                                    if type(v) in (int, float, bool, str)])
                        yield (did, round_step(ts, sync_ns), fields, *tags)
            except (KeyboardInterrupt, SystemExit):
                raise
            except ImportError:
                ts = round_step(time.time_ns(), sync_ns)
                yield (driver_id, ts, None, (TAG_ERROR, ERROR_NOLIB))
            except Exception:
                ts = round_step(time.time_ns(), sync_ns)
                yield (driver_id, ts, None, (TAG_ERROR, ERROR_EXCEP))


def main():
    if len(sys.argv) <= 1:
        print("Usage: {} <cfg_file>".format(sys.argv[0]))
        exit()
    cfg_file = sys.argv[1]

    # Read configuration
    cfg = toml.load(cfg_file)
    interval = cfg.get("interval", 0)
    host = cfg.get("host", socket.gethostname())
    inputs_cfg = cfg.get("inputs", {})
    outputs_cfg = cfg.get("outputs", {})

    # Run drivers
    with GPIOContext(inputs_cfg), contextlib.ExitStack() as stack:
        outputs = []
        for driver_id in outputs_cfg:
            for dcfg in outputs_cfg[driver_id]:
                driver_module = importlib.import_module(
                    "piot.outputs." + driver_id)
                driver = getattr(driver_module, "Driver")(**dcfg)
                outputs.append(stack.enter_context(driver))
        while True:
            for driver_id, ts, fields, *tags in collect(inputs_cfg, interval):
                if fields:
                    fields = OrderedDict([(k, v) for k, v in fields.items()
                                         if v is not None])
                dtags = OrderedDict([("host", host)] + tags)
                for output in outputs:
                    output.run(driver_id, ts, fields, dtags)


class GPIOContext:
    def __init__(self, cfg):
        GPIO.setmode(GPIO.BCM)
        pin_list = list(find(cfg, ACT_PIN_ID))
        GPIO.setup(pin_list, GPIO.OUT, initial=GPIO.HIGH)

    def close(self):
        GPIO.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class ActivationContext:
    def __init__(self, pin=None):
        self._open = False
        self._pin = pin
        if self._pin:
            self._lock = get_lock(
                "{}/gpio{}.lock".format(LOCK_PREFIX, self._pin))

    def open(self):
        if not self._pin or self._open:
            return
        self._open = True
        if self._lock:
            self._lock.acquire()
        GPIO.output(self._pin, GPIO.LOW)

    def close(self):
        if not self._pin or not self._open:
            return
        GPIO.output(self._pin, GPIO.HIGH)
        if self._lock:
            self._lock.release()
        self._open = False

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class DriverBase:
    def __init__(self, lock_file=None):
        self._open = True
        self._lock = get_lock(lock_file) if lock_file else None
        if self._lock:
            self._lock.acquire()

    def close(self):
        if not self._open:
            return
        if self._lock:
            self._lock.release()
        self._open = False

    def sid(self):
        return self.__class__.__module__.split(".")[-1]

    def run(self):
        raise NotImplementedError()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class I2CDriver(DriverBase):
    def __init__(self):
        super().__init__("{}/i2c.lock".format(LOCK_PREFIX))


class SMBusDriver(I2CDriver):
    def __init__(self, bus=1):
        super().__init__()
        self._bus = SMBus(bus)

    def close(self):
        if not self._open:
            return
        if self._bus:
            self._bus.close()
        super().close()


class SerialDriver(DriverBase):
    def __init__(self, *args, **kwargs):
        super().__init__("{}/serial.lock".format(LOCK_PREFIX))
        self._serial = Serial(timeout=1, *args, **kwargs)
        self._serial.reset_input_buffer()
        self._serial.reset_output_buffer()

    def close(self):
        if not self._open:
            return
        if self._serial:
            self._serial.close()
        super().close()

    def _cmd(self, cmd, size=0):
        self._serial.write(cmd)
        self._serial.flush()
        time.sleep(0.1)
        if size > 0:
            return self._serial.read(size)


if __name__ == "__main__":
    main()
