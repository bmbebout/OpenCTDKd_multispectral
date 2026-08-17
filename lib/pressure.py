"""Pressure module — MS5837-30BA on I2C0 (SDA=GPIO4, SCL=GPIO5).

Shares the I2C0 bus with DS3231 (0x68) and AS7341 (0x39).
MS5837-30BA address is 0x76 — no conflict.

Public API:
    setup()            -> MS5837   initialise and return sensor instance
    read(sensor)       -> (pressure_mbar, temperature_c, depth_m)
"""

from machine import I2C, Pin
from lib.ms5837 import MS5837, DENSITY_FRESHWATER, DENSITY_SALTWATER  # noqa: F401

_SDA  = 4
_SCL  = 5
_FREQ = 100_000

# Re-export density constants for callers that set fluid type
FRESHWATER = DENSITY_FRESHWATER
SALTWATER  = DENSITY_SALTWATER


def setup():
    """Initialise I2C0, verify sensor presence, read PROM calibration.
    Raises OSError if sensor not found or CRC check fails."""
    i2c = I2C(0, sda=Pin(_SDA), scl=Pin(_SCL), freq=_FREQ)
    if 0x76 not in i2c.scan():
        raise OSError("MS5837 not found on I2C0 (0x76) — check wiring")
    sensor = MS5837(i2c)
    print("Pressure: MS5837-30BA ready")
    return sensor


def read(sensor, density=DENSITY_FRESHWATER):
    """Trigger a measurement and return (pressure_mbar, temperature_c, depth_m).
    density: fluid density in kg/m³ — use FRESHWATER or SALTWATER constants."""
    sensor.read()
    return sensor.pressure, sensor.temperature, sensor.depth(density)
