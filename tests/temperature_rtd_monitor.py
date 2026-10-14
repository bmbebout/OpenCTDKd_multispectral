"""EZO-RTD vs TSYS01 continuous temperature monitor - 1 reading/s for 60 s.

Run:
    mpremote connect COM4 mount . run tests/temperature_rtd_monitor.py
"""

import time
import lib.temperature as temperature
import lib.temperature_rtd as temperature_rtd

_DURATION_S = 60


def main():
    print("=== EZO-RTD vs TSYS01 monitor (%d s) ===" % _DURATION_S)
    rtd = temperature_rtd.setup()
    tsys = temperature.setup()
    print("  rtd_C     tsys01_C  delta_C")

    deadline = time.ticks_ms() + _DURATION_S * 1000
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        start = time.ticks_ms()
        r = temperature_rtd.read(rtd)
        t = temperature.read(tsys)
        print("  %.3f    %.3f    %+.3f" % (r, t, r - t))
        pause = 1000 - time.ticks_diff(time.ticks_ms(), start)
        if pause > 0:
            time.sleep_ms(pause)

    print("Done.")


main()
