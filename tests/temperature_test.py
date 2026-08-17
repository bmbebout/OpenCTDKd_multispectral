"""TSYS01 temperature sensor bringup test.

Wiring (I2C0, shared with all other sensors):
    Celsius Red   (power) → Pico 3.3V  (pin 36)
    Celsius Black (GND)   → Pico GND   (pin 38)
    Celsius White (SDA)   → GPIO4      (pin 6)
    Celsius Green (SCL)   → GPIO5      (pin 7)

Run:
    mpremote connect COM4 mount . run tests/temperature_test.py
"""

from machine import I2C, Pin
import lib.temperature as temperature

_READS = 5


def main():
    print("=== TSYS01 temperature test ===")
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100_000)
    print("I2C scan:", [hex(a) for a in i2c.scan()])

    try:
        sensor = temperature.setup()
    except OSError as e:
        print("FAIL:", e)
        return

    print("\nTaking %d readings..." % _READS)
    print("  temp_C")
    for _ in range(_READS):
        t = temperature.read(sensor)
        print("  %.4f" % t)

    print("\nPASS")


main()
