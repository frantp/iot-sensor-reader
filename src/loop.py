#!/usr/bin/python3

import sys
import os
import time
import toml
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
            reader = getattr(sensor_module, "Reader")(**cfg[sensor])
            timestamp, fields = reader.read()
            tags = {
                "device": client._client_id,
                "sensor": sensor_id
            } 
            client.publish(format_msg(timestamp, measurement, tags, fields))
        except:
            traceback.print_exc()


if __name__ == "__main__":
    cfg_file = sys.argv[1] if len(sys.argv) >= 2 else "sreader.conf"
    device    =     os.getenv("IOTSR_DEVICE_ID", "test")
    mqtt_host =     os.getenv("IOTSR_MQTT_HOST", "localhost")
    mqtt_port = int(os.getenv("IOTSR_MQTT_PORT", "1883"))

    print("Settings:")
    print(f" - Config file: '{cfg_file}'")
    print(f" - Device ID:   '{device}'")
    print(f" - MQTT broker: '{mqtt_host}:{mqtt_port}'")

    print("Connecting to MQTT broker")

    client = mqtt.Client(device, clean_session=False)
    client.connect(mqtt_host, mqtt_port)

    print("Starting loop")

    while True:
        cfg = toml.load(cfg_file)
        interval = cfg.get("interval", 0)
        qos = cfg.get("qos", 2)
        measurement = cfg.get("measurement", "sensors")
        sensors = cfg.get("sensors", {})
        process(sensors, client, qos, measurement)
        if interval == 0:
            break
        time.sleep(interval)
