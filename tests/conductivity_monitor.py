"""EZO-EC conductivity continuous monitor — 1 reading/s for 60 s.

Run:
    mpremote connect COM4 mount . run tests/conductivity_monitor.py
"""

import time
from machine import I2C, Pin
import lib.conductivity as conductivity

_DURATION_S = 60


def main():
    print("=== EZO-EC monitor (%d s) ===" % _DURATION_S)
    sensor = conductivity.setup()
    print("  EC (uS/cm)   TDS (ppm)   Salinity (PSU)   SG")

    deadline = time.ticks_ms() + _DURATION_S * 1000
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        start = time.ticks_ms()
        ec, tds, sal, sg = conductivity.read(sensor)
        print("  %-12.2f %-11.2f %-16.4f %.4f" % (ec, tds, sal, sg))
        pause = 1000 - time.ticks_diff(time.ticks_ms(), start)
        if pause > 0:
            time.sleep_ms(pause)

    print("Done.")


main()
