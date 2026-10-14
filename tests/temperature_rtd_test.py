"""EZO-RTD temperature sensor bringup test, compared against the TSYS01.

Wiring (I2C0, shared with all other sensors):
    EZO-RTD Vcc          -> Pico 3.3V  (pin 36)
    EZO-RTD GND          -> Pico GND   (pin 38)
    EZO-RTD TX (= SDA)   -> GPIO4      (pin 6)
    EZO-RTD RX (= SCL)   -> GPIO5      (pin 7)

EZO-RTD must be in I2C mode - LED must be blue (not green).

Run:
    mpremote connect COM4 mount . run tests/temperature_rtd_test.py
"""

from machine import I2C, Pin
import lib.temperature as temperature
import lib.temperature_rtd as temperature_rtd

_READS = 5


def main():
    print("=== EZO-RTD temperature test ===")
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100_000)
    print("I2C scan:", [hex(a) for a in i2c.scan()])

    try:
        rtd = temperature_rtd.setup()
    except OSError as e:
        print("FAIL:", e)
        return

    try:
        tsys = temperature.setup()
    except OSError as e:
        print("TSYS01 unavailable (%s); showing RTD only" % e)
        tsys = None

    print("\nTaking %d readings..." % _READS)
    print("  rtd_C     tsys01_C  delta_C")
    for _ in range(_READS):
        r = temperature_rtd.read(rtd)
        if tsys is None:
            print("  %.3f" % r)
        else:
            t = temperature.read(tsys)
            print("  %.3f    %.3f    %+.3f" % (r, t, r - t))

    print("\nPASS")


main()
