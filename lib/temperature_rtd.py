"""RTD temperature module - Atlas Scientific EZO-RTD on I2C0 (SDA=GPIO4, SCL=GPIO5).

Runs in parallel with the TSYS01 temperature module (lib/temperature.py).
Shares the I2C0 bus with DS3231 (0x68), AS7341 (0x39), MS5837 (0x76), TSYS01 (0x77),
EZO-EC (0x64). EZO-RTD address is 0x66 - no conflict.

Public API:
    setup()        -> EZO_RTD  initialise and return sensor instance
    read(sensor)   -> float    temperature in degC (collects a conversion from start())
    start(sensor)  -> None     begin a conversion in the background
"""

from machine import I2C, Pin
from lib.ezo_rtd import EZO_RTD

_SDA  = 4
_SCL  = 5
_FREQ = 100_000
ADDR  = 0x66


def setup():
    """Initialise I2C0 and verify EZO-RTD presence.
    Raises OSError if sensor not found or not in I2C mode (LED must be blue)."""
    i2c = I2C(0, sda=Pin(_SDA), scl=Pin(_SCL), freq=_FREQ)
    if ADDR not in i2c.scan():
        raise OSError("EZO-RTD not found on I2C0 (0x66) - check wiring; if LED is green, switch to I2C mode first")
    sensor = EZO_RTD(i2c)
    print("Temperature: EZO-RTD ready")
    return sensor


def read(sensor):
    """Collect a reading and return temperature in degC. Raises OSError if the read fails."""
    sensor.read()
    return sensor.temperature


def start(sensor):
    """Begin a conversion so it runs while other sensors are read."""
    sensor.start()
