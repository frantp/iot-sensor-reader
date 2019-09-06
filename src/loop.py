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


def process(cfg, client, qos, measurement, pin_list=[]):
    device = client._client_id.decode("utf-8")
    for sensor in cfg:
        print("Reading sensor '{}'".format(sensor))
        try:
            GPIO.output(pin_list, GPIO.HIGH)
            scfg = cfg[sensor]
            if PIN_STR in scfg:
                GPIO.output(scfg[PIN_STR], GPIO.LOW)
                scfg = {k: v for k, v in scfg.items() if k != PIN_STR}
            sensor_module = importlib.import_module("sensors." + sensor)
            with getattr(sensor_module, "Reader")(**scfg) as reader:
                timestamp, fields = reader.read()
            if not fields:
                continue
            tags = OrderedDict([
                ("device", device),
                ("sensor", sensor)
            ])
            topic = "{}/{}/{}".format(measurement, device, sensor)
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
    measurement = cfg.get("measurement", "sensors")
    cfg_mqtt = cfg.get("mqtt", {})
    mqtt_host = cfg_mqtt.get("host", "localhost")
    mqtt_port = int(cfg_mqtt.get("port", "1883"))
    mqtt_qos = cfg_mqtt.get("qos", 2)
    cfg_sensors = cfg.get("sensors", {})

    print(f"Connecting to MQTT broker at '{mqtt_host}:{mqtt_port}'")
    client = mqtt.Client(device, clean_session=False)
    client.connect(mqtt_host, mqtt_port)
    client.loop_start()

    print("Configuring GPIO")
    PIN_STR = "ACTIVATION_PIN"
    GPIO.setmode(GPIO.BCM)
    pin_list = [cfg_sensors[sensor][PIN_STR]
        for sensor in cfg_sensors if PIN_STR in cfg_sensors[sensor]]
    GPIO.setup(pin_list, GPIO.OUT)

    print("Starting readings")
    try:
        while True:
            print("Waiting {} seconds".format(sync_time(interval)))
            time.sleep(sync_time(interval))
            process(cfg_sensors, client, mqtt_qos, measurement, pin_list)
    finally:
        GPIO.cleanup()
        client.disconnect()
