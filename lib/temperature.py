"""Temperature module — TSYS01 on I2C0 (SDA=GPIO4, SCL=GPIO5).

Shares I2C0 with DS3231 (0x68), AS7341 (0x39), MS5837 (0x76).
TSYS01 address is 0x77 — no conflict.

Public API:
    setup()        -> TSYS01   initialise and return sensor instance
    read(sensor)   -> float    temperature in °C
"""

from machine import I2C, Pin
from lib.tsys01 import TSYS01

_SDA  = 4
_SCL  = 5
_FREQ = 100_000


def setup():
    """Initialise I2C0, verify sensor presence, load PROM calibration.
    Raises OSError if sensor not found at 0x77."""
    i2c = I2C(0, sda=Pin(_SDA), scl=Pin(_SCL), freq=_FREQ)
    if 0x77 not in i2c.scan():
        raise OSError("TSYS01 not found on I2C0 (0x77) — check wiring")
    sensor = TSYS01(i2c)
    print("Temperature: TSYS01 ready")
    return sensor


def read(sensor):
    """Trigger a conversion and return temperature in °C."""
    sensor.read()
    return sensor.temperature
