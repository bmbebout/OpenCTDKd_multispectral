"""OpenCTDKd Multispectral — main entry point.

Deployed modules (lib/):
    ds3231.py  — DS3231 low-level I2C driver
    rtc.py     — RTC module (setup / read_time / set_time / read_temperature)
    sdcard.py  — SPI SD card block device driver
    storage.py — Storage module (setup / append_csv / read_file / exists)
    as7341.py  — AS7341 low-level I2C driver
    spectral.py — Spectral module (setup / read_channels)
    ms5837.py  — MS5837-30BA low-level I2C driver
    pressure.py — Pressure module (setup / read)
    tsys01.py  — TSYS01 low-level I2C driver
    temperature.py — Temperature module (setup / read)
    ezo_ec.py  — Atlas Scientific EZO-EC low-level I2C driver
    conductivity.py — Conductivity module (setup / read)
    webserver.py — WiFi AP + HTTP config server (status dashboard)

State machine modes:
    BOOT       — initialise hardware, print status
    WEB_CONFIG — serve the dashboard and manage the recording session
"""

import sys
import lib.rtc          as rtc
import lib.storage      as storage
import lib.spectral     as spectral
import lib.pressure     as pressure
import lib.temperature  as temperature
import lib.conductivity as conductivity
import lib.webserver    as webserver


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

    # --- Pressure sensor ---
    try:
        _pressure = pressure.setup()
    except OSError as e:
        print("Pressure error:", e)
        sys.exit(1)

    # --- Temperature sensor ---
    try:
        _temperature = temperature.setup()
    except OSError as e:
        print("Temperature error:", e)
        sys.exit(1)

    # --- Conductivity sensor ---
    try:
        _conductivity = conductivity.setup()
    except OSError as e:
        print("Conductivity error:", e)
        sys.exit(1)

    return _rtc, _spectral, _pressure, _temperature, _conductivity


def idle(rtc_dev, spectral_dev, pressure_dev, temp_dev, cond_dev):
    """Run the dashboard and recording loop."""
    webserver.run(rtc_dev, spectral_dev, pressure_dev, temp_dev, cond_dev)


# --- Entry point ---
rtc_dev, spectral_dev, pressure_dev, temp_dev, cond_dev = boot()
idle(rtc_dev, spectral_dev, pressure_dev, temp_dev, cond_dev)
