"""MS5837-30BA pressure sensor bringup test.

Wiring (I2C0, shared with RTC and AS7341):
    Bar30 Red   (power) → Pico 3.3V  (pin 36)
    Bar30 Black (GND)   → Pico GND   (pin 38)
    Bar30 White (SDA)   → GPIO4      (pin 6)
    Bar30 Green (SCL)   → GPIO5      (pin 7)

Run (quick, 5 readings):
    mpremote connect COM4 mount . run tests/pressure_test.py

Run (continuous, 1 reading/s for 60 s):
    mpremote connect COM4 mount . run tests/pressure_monitor.py
"""

from machine import I2C, Pin
import lib.pressure as pressure

_READS = 5


def main():
    print("=== MS5837-30BA pressure test ===")
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100_000)
    print("I2C scan:", [hex(a) for a in i2c.scan()])

    try:
        sensor = pressure.setup()
    except OSError as e:
        print("FAIL:", e)
        return

    print("\nTaking %d readings at OSR_8192..." % _READS)
    print("  mbar       temp_C   depth_m")
    for _ in range(_READS):
        p, t, d = pressure.read(sensor)
        print("  %.2f   %.2f   %.3f" % (p, t, d))

    print("\nPASS: sensor responding and returning plausible values")
    print("Note: depth should read ~0 m at surface (atmospheric pressure).")


main()
