#!/usr/bin/env python3

from drivers.utils import GPIOContext, run_drivers
from collections import OrderedDict
import paho.mqtt.client as mqtt
import socket
import sys
import time
import toml


def sync_time(interval):
    return interval - time.time() % interval if interval > 0 else 0


def format_msg(timestamp, measurement, tags, fields):
    tstr = ",".join(["{}={}".format(k, v) for k, v in tags.items()])
    fstr = ",".join(["{}={}".format(k, v) for k, v in fields.items()])
    return "{},{} {} {}".format(measurement, tstr, fstr, timestamp)


def run(cfg, measurement, host, client=None, qos=0, timestamp_sync=0):
    for driver_id, ts, fields in run_drivers(cfg, timestamp_sync):
        if fields:
            fields = OrderedDict([(k, v) \
                for k, v in fields.items() if v is not None])
        if not fields:
            continue
        tags = OrderedDict([
            ("host", host),
            ("sid", driver_id),
        ])
        payload = format_msg(ts, measurement, tags, fields)
        if client:
            topic = "{}/{}/{}".format(measurement, host, driver_id)
            client.publish(topic, payload, qos, True)
        else:
            print(payload)


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Usage: {} <cfg_file>".format(sys.argv[0]))
    cfg_file  = sys.argv[1]

    # Read configuration
    cfg = toml.load(cfg_file)
    interval = cfg.get("interval", 0)
    measurement = cfg.get("measurement", "data")
    host = cfg.get("host", socket.gethostname())
    common_timestamp = cfg.get("common_timestamp", False)
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
                time.sleep(sync_time(interval))
                run(drivers_cfg, measurement, host,
                    mqtt_client, mqtt_qos, interval)
    finally:
        if mqtt_client:
            mqtt_client.disconnect()
