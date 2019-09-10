#!/usr/bin/env python3

from collections import OrderedDict
import importlib
import sys
import toml
import traceback

import RPi.GPIO as GPIO


def format_msg(timestamp, measurement, fields):
    fstr = ",".join(["{}={}".format(k, v) for k, v in fields.items()])
    return "{} {} {}".format(measurement, fstr, timestamp)


def run(cfg):
    PIN_STR = "ACTIVATION_PIN"
    GPIO.setmode(GPIO.BCM)
    pin_list = [driver_cfg[PIN_STR]
        for driver_id in cfg
        for driver_cfg in cfg[driver_id] if PIN_STR in driver_cfg]
    GPIO.setup(pin_list, GPIO.OUT, initial=GPIO.HIGH)
    for driver_id in cfg:
        try:
            for dcfg in cfg[driver_id]:
                activation_pin = None
                if PIN_STR in dcfg:
                    activation_pin = dcfg[PIN_STR]
                    dcfg = {k: v for k, v in dcfg.items() if k != PIN_STR}
                driver_module = importlib.import_module("drivers." + driver_id)
                driver_class = getattr(driver_module, "Driver")
                with driver_class(**dcfg).activate(activation_pin) as driver:
                    timestamp, fields = driver.run()
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
    try:
        run(toml.load(cfg_file))
    finally:
        GPIO.cleanup()
