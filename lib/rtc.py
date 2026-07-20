"""RTC module — DS3231 on I2C0 (SDA=GPIO4, SCL=GPIO5).

Public API:
    setup()             -> DS3231 instance (call once at startup)
    read_time(rtc)      -> (year, month, day, hour, minute, second)
    set_time(rtc, ...)  -> None
    read_temperature(rtc) -> float (°C)
"""

from machine import I2C, Pin
from ds3231 import DS3231

_SDA = 4
_SCL = 5
_FREQ = 100_000


def setup():
    """Initialise I2C0 and return a DS3231 instance. Raises OSError if not found."""
    i2c = I2C(0, sda=Pin(_SDA), scl=Pin(_SCL), freq=_FREQ)
    if 0x68 not in i2c.scan():
        raise OSError("DS3231 not found on I2C0 (0x68) — check wiring")
    return DS3231(i2c)


def read_time(rtc):
    """Return (year, month, day, hour, minute, second)."""
    y, mo, d, h, mi, s, _ = rtc.get_datetime()
    return (y, mo, d, h, mi, s)


def set_time(rtc, year, month, day, hour, minute, second):
    """Write datetime to the RTC."""
    rtc.set_datetime(year, month, day, hour, minute, second)


def read_temperature(rtc):
    """Return DS3231 internal temperature in °C."""
    return rtc.temperature()
