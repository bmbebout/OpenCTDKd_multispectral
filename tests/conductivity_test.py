"""EZO-EC conductivity sensor bringup test.

Wiring (I2C0, shared with RTC, AS7341, MS5837, TSYS01):
    Carrier board VCC → Pico 2W 3.3V  (pin 36)
    Carrier board GND → Pico 2W GND   (pin 38)
    Carrier board SDA → GPIO4         (pin 6)
    Carrier board SCL → GPIO5         (pin 7)

Prerequisites:
    EZO-EC must be in I2C mode — LED must be solid blue (not blinking green).
    If LED is green (UART mode), switch to I2C first:
        Option A (software): send "I2C,98" via a serial terminal while in UART mode
        Option B (hardware): short PGND pin to TX pin with a jumper during power-up

Run (quick, 5 readings):
    mpremote connect COM4 mount . run tests/conductivity_test.py
"""

from machine import I2C, Pin
import lib.conductivity as conductivity

_READS = 5


def main():
    print("=== EZO-EC conductivity test ===")
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100_000)
    print("I2C scan:", [hex(a) for a in i2c.scan()])

    try:
        sensor = conductivity.setup()
    except OSError as e:
        print("FAIL:", e)
        return

    print("\nTaking %d readings (no temperature compensation)..." % _READS)
    print("  EC (uS/cm)   TDS (ppm)   Salinity (PSU)   SG")
    for _ in range(_READS):
        ec, tds, sal, sg = conductivity.read(sensor)
        print("  %-12.2f %-11.2f %-16.4f %.4f" % (ec, tds, sal, sg))

    print("\nPASS: sensor responding and returning values")
    print("Note: probe in air will read ~0 uS/cm — this is normal.")


main()
