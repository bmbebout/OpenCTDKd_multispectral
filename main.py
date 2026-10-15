"""OpenCTDKd Multispectral — main entry point.

Deployed modules (lib/):
    ds3231.py  — DS3231 low-level I2C driver
    rtc.py     — RTC module (setup / read_time / set_time / read_temperature)
    sdcard.py  — SPI SD card block device driver
    storage.py — Storage module (setup / append_csv / read_file / exists)
    as7341.py  — AS7341 low-level I2C driver
    spectral.py — Spectral module (setup / read)
    ms5837.py  — MS5837-30BA low-level I2C driver
    pressure.py — Pressure module (setup / read)
    tsys01.py  — TSYS01 low-level I2C driver
    temperature.py — Temperature module (setup / read)
    ezo_rtd.py  — Atlas Scientific EZO-RTD low-level I2C driver
    temperature_rtd.py — RTD temperature module (setup / read / start)
    sensors.py  — Sensor lifecycle (lazy setup, retry, health) and shared sampling (read_all; failed values are ERR)
    ezo_ec.py  — Atlas Scientific EZO-EC low-level I2C driver
    conductivity.py — Conductivity module (setup / read)
    neo6m.py    — NEO-6M-compatible NMEA GPS driver
    gps.py      — GPS module (setup / read / RTC sync)
    oled.py     — SSD1306 128x32 OLED module
    webserver.py — WiFi AP + HTTP config server (status dashboard)

State machine modes:
    BOOT       — initialise hardware, print status
    WEB_CONFIG — serve the dashboard and manage the recording session
"""

import sys
import time
import lib.rtc          as rtc
import lib.storage      as storage
import lib.spectral     as spectral
import lib.pressure     as pressure
import lib.temperature  as temperature
import lib.temperature_rtd as temperature_rtd
import lib.conductivity as conductivity
import lib.gps          as gps
import lib.oled         as oled
import lib.recording    as recording
import lib.sensors      as sensors
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
    sd_ready = False
    for attempt in range(3):
        try:
            storage.setup()
            sd_ready = True
            break
        except OSError as e:
            print("SD error (attempt %d/3):" % (attempt + 1), e)
            time.sleep(1)
    if not sd_ready:
        print("SD unavailable; web server will start, but recording and file operations are disabled")
    else:
        try:
            storage.append_log("boot", _fmt_time(rtc.read_time(_rtc)).replace("  ", "T"))
        except OSError as e:
            print("Log error:", e)

    # --- GPS ---
    _gps = None
    rtc_source = "rtc"
    try:
        _gps = gps.setup()
        print("GPS:   waiting for first fix; RTC source:", rtc_source)
    except OSError as e:
        print("GPS error:", e)
        _gps = None

    # --- Sensors: set up lazily; a sensor that fails is retried later and records ERR meanwhile ---
    sensors.set_event_logger(lambda message: recording.log_event(message, _rtc))
    _spectral     = sensors.Sensor("AS7341", spectral, spectral.ADDR)
    _pressure     = sensors.Sensor("MS5837", pressure, pressure.ADDR)
    _temperature  = sensors.Sensor("TSYS01", temperature, temperature.ADDR)
    _rtd          = sensors.Sensor("EZO-RTD", temperature_rtd, temperature_rtd.ADDR)
    _conductivity = sensors.Sensor("EZO-EC", conductivity, conductivity.ADDR)
    for sensor in (_spectral, _pressure, _temperature, _rtd, _conductivity):
        sensor.attempt(force=True)

    try:
        _oled = oled.setup()
    except OSError as e:
        print("OLED error:", e)
        _oled = None

    return _rtc, _gps, rtc_source, _spectral, _pressure, _temperature, _rtd, _conductivity, _oled


def idle(rtc_dev, gps_dev, rtc_source, spectral_dev, pressure_dev, temp_dev, rtd_dev, cond_dev, oled_dev):
    """Run the dashboard and recording loop."""
    webserver.run(rtc_dev, gps_dev, rtc_source, spectral_dev, pressure_dev, temp_dev, rtd_dev, cond_dev, oled_dev)


# --- Entry point ---
rtc_dev, gps_dev, rtc_source, spectral_dev, pressure_dev, temp_dev, rtd_dev, cond_dev, oled_dev = boot()
idle(rtc_dev, gps_dev, rtc_source, spectral_dev, pressure_dev, temp_dev, rtd_dev, cond_dev, oled_dev)
