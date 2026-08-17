"""TSYS01 continuous temperature monitor — 1 reading/s for 60 s.

Run:
    mpremote connect COM4 mount . run tests/temperature_monitor.py
"""

import time
from machine import I2C, Pin
import lib.temperature as temperature

_DURATION_S = 60


def main():
    print("=== TSYS01 monitor (%d s) ===" % _DURATION_S)
    sensor = temperature.setup()
    print("  temp_C")

    deadline = time.ticks_ms() + _DURATION_S * 1000
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        start = time.ticks_ms()
        t = temperature.read(sensor)
        print("  %.4f" % t)
        pause = 1000 - time.ticks_diff(time.ticks_ms(), start)
        if pause > 0:
            time.sleep_ms(pause)

    print("Done.")


main()
