#!/usr/bin/env python3

import importlib
import os
import socket
import sys
import time
import toml
import traceback

import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt


def format_msg(timestamp, measurement, tags, fields):
    tstr = ",".join(["{}={}".format(k, v) for k, v in tags.items()])
    fstr = ",".join(["{}={}".format(k, v) for k, v in fields.items()])
    return "{},{} {} {}".format(measurement, tstr, fstr, timestamp)


def process(cfg, client, qos, measurement):
    PIN_STR = "ACTIVATION_PIN"
    pin_list = [cfg[sensor][PIN_STR]
        for sensor in cfg if PIN_STR in cfg[sensor]]
    GPIO.setup(pin_list, GPIO.OUT)
    for sensor in cfg:
        try:
            GPIO.output(pin_list, GPIO.HIGH)
            scfg = cfg[sensor]
            if PIN_STR in scfg:
                GPIO.output(scfg[PIN_STR], GPIO.LOW)
                scfg = {k: v for k, v in scfg.items() if k != PIN_STR}
            sensor_module = importlib.import_module("sensors." + sensor)
            with getattr(sensor_module, "Reader")(**scfg) as reader:
                timestamp, fields = reader.read()
            tags = {
                "device": client._client_id,
                "sensor": sensor
            } 
            client.publish("sensors",
                format_msg(timestamp, measurement, tags, fields), qos=qos)
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

    print("Connecting to MQTT broker")

    client = mqtt.Client(device, clean_session=False)
    client.connect(mqtt_host, mqtt_port)

    print("Starting readings")

    GPIO.setmode(GPIO.BCM)
    try:
        while True:
            time.sleep(interval - time.time() % interval)
            process(cfg_sensors, client, mqtt_qos, measurement)
    finally:
        GPIO.cleanup()
