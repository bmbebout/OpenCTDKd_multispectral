"""Spectral module — AS7341 on I2C0 (SDA=GPIO4, SCL=GPIO5).

Shares the I2C0 bus with the RTC (DS3231 at 0x68).
AS7341 address is 0x39 — no conflict.

Public API:
    setup()               -> AS7341  initialise and return sensor instance
    read_channels(sensor) -> dict    10 raw ADC counts keyed by channel name
"""

from machine import I2C, Pin
from lib.as7341 import AS7341

_SDA  = 4
_SCL  = 5
_FREQ = 100_000

# Ordered channel list — useful for CSV headers and iteration
CHANNEL_NAMES = [
    "F1_415nm", "F2_445nm", "F3_480nm", "F4_515nm",
    "F5_555nm", "F6_590nm", "F7_630nm", "F8_680nm",
    "clear", "nir",
]


def setup():
    """Initialise I2C0 and return an AS7341 instance.
    Raises OSError if the sensor is not found at 0x39."""
    # TODO: refactor to accept a shared I2C bus instance once all I2C
    # sensors are integrated (avoids multiple objects on the same hardware bus)
    i2c = I2C(0, sda=Pin(_SDA), scl=Pin(_SCL), freq=_FREQ)
    if 0x39 not in i2c.scan():
        raise OSError("AS7341 not found on I2C0 (0x39) — check wiring")
    sensor = AS7341(i2c)
    print("Spectral: AS7341 ready")
    return sensor


def read_channels(sensor):
    """Read all 10 spectral channels.  Returns a dict of raw 16-bit counts.
    Two SMUX measurement passes are performed internally (~280 ms total
    with default ATIME=100, ASTEP=500)."""
    return sensor.read_all_channels()
