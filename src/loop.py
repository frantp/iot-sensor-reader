#!/usr/bin/env python3

from collections import OrderedDict
import importlib
import os
import socket
import sys
import time
import toml
import traceback

import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt


def sync_time(interval):
    return interval - time.time() % interval


def format_msg(timestamp, measurement, tags, fields):
    tstr = ",".join(["{}={}".format(k, v) for k, v in tags.items()])
    fstr = ",".join(["{}={}".format(k, v) for k, v in fields.items()])
    return "{},{} {} {}".format(measurement, tstr, fstr, timestamp)


def run(cfg, client, qos, measurement, pin_list=[]):
    device_id = client._client_id.decode("utf-8")
    for driver_id in cfg:
        print("Running driver '{}'".format(driver_id))
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
            topic = "{}/{}/{}".format(measurement, device_id, driver_id)
            payload = format_msg(timestamp, measurement, tags, fields)
            client.publish(topic, payload, qos)
        except:
            traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Usage: {} <cfg_file>".format(sys.argv[0]))
    cfg_file  = sys.argv[1]

    print("Reading configuration")
    cfg = toml.load(cfg_file)
    interval = int(cfg.get("interval", "5"))
    device = cfg.get("device") or socket.gethostname()
    measurement = cfg.get("measurement", "data")
    cfg_mqtt = cfg.get("mqtt", {})
    mqtt_host = cfg_mqtt.get("host", "localhost")
    mqtt_port = int(cfg_mqtt.get("port", "1883"))
    mqtt_qos = cfg_mqtt.get("qos", 2)
    cfg_drivers = cfg.get("drivers", {})

    print(f"Connecting to MQTT broker at '{mqtt_host}:{mqtt_port}'")
    client = mqtt.Client(device, clean_session=False)
    client.connect(mqtt_host, mqtt_port)
    client.loop_start()

    print("Configuring GPIO")
    PIN_STR = "ACTIVATION_PIN"
    GPIO.setmode(GPIO.BCM)
    pin_list = [cfg_drivers[driver_id][PIN_STR]
        for driver_id in cfg_drivers if PIN_STR in cfg_drivers[driver_id]]
    GPIO.setup(pin_list, GPIO.OUT)

    print("Starting readings")
    try:
        while True:
            print("Waiting {} seconds".format(sync_time(interval)))
            time.sleep(sync_time(interval))
            run(cfg_drivers, client, mqtt_qos, measurement, pin_list)
    finally:
        GPIO.cleanup()
        client.disconnect()
