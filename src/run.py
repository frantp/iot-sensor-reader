#!/usr/bin/env python3

from collections import OrderedDict
import importlib
import os
import socket
import sys
import toml
import traceback

import RPi.GPIO as GPIO


def format_msg(timestamp, measurement, tags, fields):
    tstr = ",".join(["{}={}".format(k, v) for k, v in tags.items()])
    fstr = ",".join(["{}={}".format(k, v) for k, v in fields.items()])
    return "{},{} {} {}".format(measurement, tstr, fstr, timestamp)


def run(cfg, device_id, measurement, pin_list=[]):
    for driver_id in cfg:
        try:
            GPIO.output(pin_list, GPIO.HIGH)
            dcfg = cfg[driver_id]
            if PIN_STR in dcfg:
                GPIO.output(dcfg[PIN_STR], GPIO.LOW)
                dcfg = {k: v for k, v in dcfg.items() if k != PIN_STR}
            driver_module = importlib.import_module("drivers." + driver_id)
            with getattr(driver_module, "Driver")(**dcfg) as driver:
                timestamp, fields = driver.run()
            if not fields:
                continue
            tags = OrderedDict([
                ("device", device_id),
                ("sensor", driver_id)
            ])
            print(format_msg(timestamp, measurement, tags, fields))
        except:
            traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Usage: {} <cfg_file>".format(sys.argv[0]))
    cfg_file  = sys.argv[1]

    # Read configuration
    cfg = toml.load(cfg_file)
    interval = int(cfg.get("interval", "5"))
    device_id = cfg.get("device") or socket.gethostname()
    measurement = cfg.get("measurement", "data")
    cfg_drivers = cfg.get("drivers", {})

    # Configure GPIO
    PIN_STR = "ACTIVATION_PIN"
    GPIO.setmode(GPIO.BCM)
    pin_list = [cfg_drivers[driver_id][PIN_STR]
        for driver_id in cfg_drivers if PIN_STR in cfg_drivers[driver_id]]
    GPIO.setup(pin_list, GPIO.OUT)

    # Run drivers
    try:
        run(cfg_drivers, device_id, measurement, pin_list)
    finally:
        GPIO.cleanup()
