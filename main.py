"""OpenCTDKd Multispectral — main entry point.

Deployed modules (lib/):
    ds3231.py  — DS3231 low-level I2C driver
    rtc.py     — RTC module (setup / read_time / set_time / read_temperature)

State machine modes (to be expanded as hardware is added):
    BOOT  — initialise hardware, print status, then transition to IDLE
    IDLE  — placeholder; will become the logging/standby loop
"""

import sys
import lib.rtc as rtc


def _fmt_time(t):
    return "%04d-%02d-%02d  %02d:%02d:%02d" % t


def boot():
    print("OpenCTDKd booting...")

    # --- RTC ---
    try:
        _rtc = rtc.setup()
        t = rtc.read_time(_rtc)
        print("RTC:  ", _fmt_time(t))
        print("Temp: ", rtc.read_temperature(_rtc), "C")
    except OSError as e:
        print("RTC error:", e)
        sys.exit(1)

    return _rtc


def idle(rtc_dev):
    """Placeholder idle loop — will grow into the main logging state machine."""
    print("System ready. (idle)")


# --- Entry point ---
rtc_dev = boot()
idle(rtc_dev)
