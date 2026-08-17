"""OpenCTDKd Multispectral — main entry point.

Deployed modules (lib/):
    ds3231.py  — DS3231 low-level I2C driver
    rtc.py     — RTC module (setup / read_time / set_time / read_temperature)
    sdcard.py  — SPI SD card block device driver
    storage.py — Storage module (setup / append_csv / read_file / exists)
    as7341.py  — AS7341 low-level I2C driver
    spectral.py — Spectral module (setup / read_channels)

State machine modes (to be expanded as hardware is added):
    BOOT  — initialise hardware, print status, then transition to IDLE
    IDLE  — placeholder; will become the logging/standby loop
"""

import sys
import lib.rtc as rtc
import lib.storage as storage
import lib.spectral as spectral


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

    # --- SD card ---
    try:
        storage.setup()
    except OSError as e:
        print("SD error:", e)
        sys.exit(1)

    # --- Spectral sensor ---
    try:
        _spectral = spectral.setup()
    except OSError as e:
        print("Spectral error:", e)
        sys.exit(1)

    return _rtc, _spectral


def idle(rtc_dev, spectral_dev):
    """Placeholder idle loop — will grow into the main logging state machine."""
    print("System ready. (idle)")


# --- Entry point ---
rtc_dev, spectral_dev = boot()
idle(rtc_dev, spectral_dev)
