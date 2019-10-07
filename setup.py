import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="piot",
    version="0.0.4",
    author="Francisco Troncoso Pastoriza",
    author_email="frantp90@gmail.com",
    description="Load and run device drivers at specific intervals, mainly sensor reading",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/frantp/piot",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    keywords="driver sensor reading",
    install_requires=[
        "toml",
        "paho-mqtt",
        "filelock",
        "RPi.GPIO",
        "smbus2",
        "pyserial",
        "adafruit-circuitpython-adxl34x",
        "adafruit-circuitpython-amg88xx",
        "adafruit-circuitpython-bme280",
        "adafruit-circuitpython-bme680",
        "adafruit-circuitpython-dht",
        "adafruit-circuitpython-hcsr04",
        "adafruit-circuitpython-mlx90614",
        "adafruit-circuitpython-tsl2561",
        "adafruit-circuitpython-tsl2591",
        "Adafruit-SSD1306",
        "Pillow",
        "pypozyx-i2c",
    ],
    python_requires=">=3.5",
    entry_points={
        "console_scripts": [
            "piot = piot.core:main"
        ],
    },
)
