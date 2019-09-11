#!/usr/bin/env python3

from drivers.base import ActivationContext
from collections import OrderedDict
import importlib
import RPi.GPIO as GPIO
import sys
import time
import toml
import traceback


PIN_STR = "ACTIVATION_PIN"


def sync_time(interval):
    return interval - time.time() % interval if interval > 0 else 0

def format_msg(timestamp, measurement, fields):
    fstr = ",".join(["{}={}".format(k, v) for k, v in fields.items()])
    return "{} {} {}".format(measurement, fstr, timestamp)


def run(cfg):
    for driver_id in cfg:
        try:
            for dcfg in cfg[driver_id]:
                activation_pin = None
                if PIN_STR in dcfg:
                    activation_pin = dcfg[PIN_STR]
                    dcfg = {k: v for k, v in dcfg.items() if k != PIN_STR}
                driver_module = importlib.import_module("drivers." + driver_id)
                with ActivationContext(activation_pin), \
                     getattr(driver_module, "Driver")(**dcfg) as driver:
                    res = driver.run()
                for timestamp, fields in res:
                    if fields:
                        fields = OrderedDict([(k, v) for k, v in fields.items() \
                            if v is not None])
                    if not fields:
                        continue
                    print(format_msg(timestamp, driver_id, fields))
        except:
            traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Usage: {} <cfg_file>".format(sys.argv[0]))
    cfg_file  = sys.argv[1]

    # Read configuration
    cfg = toml.load(cfg_file)
    interval = int(cfg.get("interval", "0"))
    drivers_cfg = cfg.get("drivers", {})

    # Configure GPIO
    GPIO.setmode(GPIO.BCM)
    pin_list = [driver_cfg[PIN_STR]
        for driver_id in drivers_cfg
        for driver_cfg in drivers_cfg[driver_id] if PIN_STR in driver_cfg]
    GPIO.setup(pin_list, GPIO.OUT, initial=GPIO.HIGH)

    # Run drivers
    try:
        while True:
            time.sleep(sync_time(interval))
            run(drivers_cfg)
    finally:
        GPIO.cleanup()
