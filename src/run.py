#!/usr/bin/env python3

import drivers.utils
from collections import OrderedDict
import sys
import time
import toml


def sync_time(interval):
    return interval - time.time() % interval if interval > 0 else 0


def format_msg(timestamp, measurement, fields):
    fstr = ",".join(["{}={}".format(k, v) for k, v in fields.items()])
    return "{} {} {}".format(measurement, fstr, timestamp)


def run(cfg):
    for driver_id, tm, fields in drivers.utils.run_drivers(cfg):
        if fields:
            fields = OrderedDict([(k, v) \
                for k, v in fields.items() if v is not None])
        if not fields:
            continue
        print(format_msg(tm, driver_id, fields))


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Usage: {} <cfg_file>".format(sys.argv[0]))
    cfg_file  = sys.argv[1]

    # Read configuration
    cfg = toml.load(cfg_file)
    interval = int(cfg.get("interval", "0"))
    drivers_cfg = cfg.get("drivers", {})

    # Run drivers
    with drivers.utils.GPIOContext(drivers_cfg):
        while True:
            time.sleep(sync_time(interval))
            run(drivers_cfg)
