"""MS5837-30BA continuous monitor — 1 reading/s for 60 s.

Run:
    mpremote connect COM4 mount . run tests/pressure_monitor.py
"""

import time
from machine import I2C, Pin
import lib.pressure as pressure

_DURATION_S = 60


def main():
    print("=== MS5837-30BA monitor (%d s) ===" % _DURATION_S)
    sensor = pressure.setup()
    print("  mbar       temp_C   depth_m")

    deadline = time.ticks_ms() + _DURATION_S * 1000
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        start = time.ticks_ms()
        p, t, d = pressure.read(sensor)
        print("  %.2f   %.2f   %.3f" % (p, t, d))
        pause = 1000 - time.ticks_diff(time.ticks_ms(), start)
        if pause > 0:
            time.sleep_ms(pause)

    print("Done.")


main()
