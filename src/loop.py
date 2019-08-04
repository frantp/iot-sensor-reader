#!/usr/bin/python3

import sys
import os
import time
import yaml
import paho.mqtt.client as mqtt
import importlib
import traceback


def format_msg(timestamp, measurement, tags, fields):
    tstr = ",".join([f"{k}={v}" for k, v in tags.items()])
    fstr = ",".join([f"{k}={v}" for k, v in fields.items()])
    return f"{measurement},{tstr} {fstr} {timestamp}"


def process(cfg, client, qos, measurement):
    for sensor in cfg:
        sensor_id = sensor.split("_", 1)[0]
        try:
            sensor_module = importlib.import_module(f"sensors.{sensor}")
            reader = getattr(sensor_module, "Reader")(**cfg[sensor]["init"])
            timestamp, fields = reader.read(**cfg[sensor]["read"])
            tags = {
                "device": client._client_id,
                "sensor": sensor_id
            } 
            client.publish(format_msg(timestamp, measurement, tags, fields))
        except:
            traceback.print_exc()


if __name__ == "__main__":
    cfg_file = sys.argv[1] if len(sys.argv) >= 2 else "sreader.yml"
    interval    = float(os.getenv("IOTSR_INTERVAL" , "5"))
    device      =       os.getenv("IOTSR_DEVICE_ID", "test")
    mqtt_host   =       os.getenv("IOTSR_MQTT_HOST", "localhost")
    mqtt_port   =   int(os.getenv("IOTSR_MQTT_PORT", "1883"))
    mqtt_qos    =   int(os.getenv("IOTSR_MQTT_QOS" , "2"))
    measurement =       os.getenv("IOTSR_MQTT_MEAS", "sensors")

    print("Settings:")
    print(f" - Config file: '{cfg_file}'")
    print(f" - Interval:    {interval} s")
    print(f" - Device ID:   '{device}'")
    print(f" - MQTT Host:   '{mqtt_host}:{mqtt_port}'")
    print(f" - MQTT QoS:    {mqtt_qos}")
    print(f" - Measurement: '{measurement}'")

    print("Connecting to MQTT broker")

    client = mqtt.Client(device, clean_session=False)
    client.connect(mqtt_host, mqtt_port)

    print("Starting loop")

    while True:
        with open(cfg_file, "r") as f:
            cfg = yaml.safe_load(f)
        process(cfg, client, mqtt_qos, measurement)
        if interval == 0:
            break
        time.sleep(interval)
