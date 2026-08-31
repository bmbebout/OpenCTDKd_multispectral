"""Conductivity module — Atlas Scientific EZO-EC on I2C0 (SDA=GPIO4, SCL=GPIO5).

Shares the I2C0 bus with DS3231 (0x68), AS7341 (0x39), MS5837 (0x76), TSYS01 (0x77).
EZO-EC address is 0x62 — no conflict.

Public API:
    setup()                              -> EZO_EC   initialise and return sensor instance
    read(sensor, temperature_c=None)     -> (ec_us_cm, tds_ppm, salinity_psu, specific_gravity)
"""

from machine import I2C, Pin
from lib.ezo_ec import EZO_EC

_SDA  = 4
_SCL  = 5
_FREQ = 100_000


def setup():
    """Initialise I2C0 and verify EZO-EC presence.
    Raises OSError if sensor not found or not in I2C mode (LED must be solid blue)."""
    i2c = I2C(0, sda=Pin(_SDA), scl=Pin(_SCL), freq=_FREQ)
    if 0x64 not in i2c.scan():
        raise OSError("EZO-EC not found on I2C0 (0x64) — check wiring; if LED is green, switch to I2C mode first")
    sensor = EZO_EC(i2c)
    print("Conductivity: EZO-EC ready")
    return sensor


def read(sensor, temperature_c=None):
    """Trigger a reading; return (ec_us_cm, tds_ppm, salinity_psu, specific_gravity).
    temperature_c: pass TSYS01 reading for temperature-compensated EC."""
    sensor.read(temperature_c)
    return sensor.ec, sensor.tds, sensor.salinity, sensor.specific_gravity
