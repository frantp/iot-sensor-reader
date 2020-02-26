#!/usr/bin/env python3

from collections import OrderedDict
from filelock import FileLock
import importlib
import os
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
from serial import Serial
from smbus2 import SMBus
import socket
import sys
import time
import toml
import traceback


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
    fstr = ",".join(["{0}={3}{1}{2}{3}".format(k, v,
        "i"  if isinstance(v, int) else "",
        "\"" if isinstance(v, str) else "") for k, v in fields.items()])
    return "{},{} {} {}".format(measurement, tstr, fstr, timestamp)


def sync_wait(sync):
    return sync - time.time() % sync if sync > 0 else 0


def round_step(x, step):
    return x // step * step if step else x


def run_drivers(cfg, sync=0):
    sync_ns = int(sync * 1e9)
    time.sleep(sync_wait(sync))
    for driver_id in cfg:
        try:
            for dcfg in cfg[driver_id]:
                activation_pin = None
                if ACT_PIN_ID in dcfg:
                    activation_pin = dcfg[ACT_PIN_ID]
                    dcfg = {k: v for k, v in dcfg.items() if k != ACT_PIN_ID}
                driver_module = importlib.import_module(
                    "piot.drivers." + driver_id)
                with ActivationContext(activation_pin), \
                     getattr(driver_module, "Driver")(**dcfg) as driver:
                    res = driver.run()
                    if not res:
                        continue
                    for did, ts, fields, *tags in res:
                        tags.extend([(driver_id + "." + k, v)
                            for k, v in dcfg.items() if type(v) in (int, float, bool, str)])
                        yield (did, round_step(ts, sync_ns), fields, *tags)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            traceback.print_exc()


def run(cfg, host, client=None, qos=0, sync=0):
    for driver_id, ts, fields, *tags in run_drivers(cfg, sync):
        if fields:
            fields = OrderedDict([(k, v) \
                for k, v in fields.items() if v is not None])
        if not fields:
            continue
        dtags = OrderedDict([("host", host)] + tags)
        payload = format_msg(ts, driver_id, dtags, fields)
        if client:
            topic = "data/{}/{}".format(host, driver_id)
            client.publish(topic, payload, qos, True)
        else:
            print(payload)


def main():
    if len(sys.argv) <= 1:
        print("Usage: {} <cfg_file>".format(sys.argv[0]))
        exit()
    cfg_file = sys.argv[1]

    # Read configuration
    cfg = toml.load(cfg_file)
    interval = cfg.get("interval", 0)
    host = cfg.get("host", socket.gethostname())
    drivers_cfg = cfg.get("drivers", {})

    # Connect to MQTT broker, if necessary
    mqtt_client, mqtt_qos = None, 0
    mqtt_cfg = cfg.get("mqtt", None)
    if mqtt_cfg is not None:
        mqtt_host = mqtt_cfg.get("host", "localhost")
        mqtt_port = mqtt_cfg.get("port", 1883)
        mqtt_qos = mqtt_cfg.get("qos", 2)
        print(f"Connecting to MQTT broker at '{mqtt_host}:{mqtt_port}'")
        mqtt_client = mqtt.Client(host, clean_session=False)
        mqtt_client.connect(mqtt_host, mqtt_port)
        mqtt_client.loop_start()

    # Run drivers
    try:
        with GPIOContext(drivers_cfg):
            while True:
                run(drivers_cfg, host, mqtt_client, mqtt_qos, interval)
    finally:
        if mqtt_client:
            mqtt_client.disconnect()


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
        if self._lock: self._lock.acquire()
        GPIO.output(self._pin, GPIO.LOW)


    def close(self):
        if not self._pin or not self._open:
            return
        GPIO.output(self._pin, GPIO.HIGH)
        if self._lock: self._lock.release()
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
        if self._lock: self._lock.acquire()


    def close(self):
        if not self._open:
            return
        if self._lock: self._lock.release()
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
        if self._bus: self._bus.close()
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
        if self._serial: self._serial.close()
        super().close()


    def _cmd(self, cmd, size=0):
        self._serial.write(cmd)
        self._serial.flush()
        time.sleep(0.1)
        if size > 0:
            return self._serial.read(size)


if __name__ == "__main__":
    main()
