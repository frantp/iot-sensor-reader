#!/usr/bin/python3

import sys
import os
import time
import toml
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import importlib
import traceback


def format_msg(timestamp, measurement, tags, fields):
    tstr = ",".join([f"{k}={v}" for k, v in tags.items()])
    fstr = ",".join([f"{k}={v}" for k, v in fields.items()])
    return f"{measurement},{tstr} {fstr} {timestamp}"


def process(cfg, client, qos, measurement):
    PIN_STR = "ACTIVATION_PIN"
    pin_list = [cfg[sensor][PIN_STR]
        for sensor in cfg if PIN_STR in cfg[sensor]]
    GPIO.setup(pin_list, GPIO.OUT)
    for sensor in cfg:
        sensor_id = sensor.split("_", 1)[0]
        try:
            GPIO.output(pin_list, GPIO.HIGH)
            scfg = cfg[sensor]
            if PIN_STR in scfg:
                GPIO.output(scfg[PIN_STR], GPIO.LOW)
                scfg = {k: v for k, v in scfg.items() if k != PIN_STR}
            sensor_module = importlib.import_module(f"sensors.{sensor}")
            with getattr(sensor_module, "Reader")(**scfg) as reader:
                timestamp, fields = reader.read()
            tags = {
                "device": client._client_id,
                "sensor": sensor_id
            } 
            client.publish(format_msg(timestamp, measurement, tags, fields))
        except:
            traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print(f"Usage: {sys.argv[0]} <cfg_file> [device_id]")
    cfg_file  = sys.argv[1]
    device    = sys.argv[2] if len(sys.argv) > 2 else \
                    os.getenv("IOTSR_DEVICE_ID", "test")
    mqtt_host =     os.getenv("IOTSR_MQTT_HOST", "localhost")
    mqtt_port = int(os.getenv("IOTSR_MQTT_PORT", "1883"))

    print("Settings:")
    print(f" - Config file: '{cfg_file}'")
    print(f" - Device ID:   '{device}'")
    print(f" - MQTT broker: '{mqtt_host}:{mqtt_port}'")

    print("Connecting to MQTT broker")

    client = mqtt.Client(device, clean_session=False)
    client.connect(mqtt_host, mqtt_port)

    print("Starting readings")

    GPIO.setmode(GPIO.BCM)

    try:
        while True:
            cfg = toml.load(cfg_file)
            interval = cfg.get("interval", 0)
            if interval > 0:
                time.sleep(interval - time.time() % interval)

            cfg = toml.load(cfg_file)
            qos = cfg.get("qos", 2)
            measurement = cfg.get("measurement", "sensors")
            sensors = cfg.get("sensors", {})
            process(sensors, client, qos, measurement)

            if interval <= 0:
                break

    finally:
        GPIO.cleanup()
