"""CSV recording session for the OpenCTDKd sensor set."""

import os
import time
from machine import Pin

import lib.storage as _storage
import lib.rtc as _rtc
import lib.spectral as _spectral
import lib.pressure as _pressure
import lib.temperature as _temp
import lib.conductivity as _cond

_HEADER = [
    "Date", "Time", "Pressure", "Depth", "Temp", "Conductivity",
    "TDS", "Salinity", "Specific Gravity", "F1_415nm", "F2_445nm",
    "F3_480nm", "F4_515nm", "F5_555nm", "F6_590nm", "F7_630nm",
    "F8_680nm", "Clear", "NIR",
]

_path = None
_active = False
_last_sample = 0
_interval_ms = 1000
_sqw = None
_sqw_ticks = 0
_sqw_count = 0
_sqw_seen = 0


def _sqw_irq(pin):
    global _sqw_ticks, _sqw_count
    _sqw_ticks = time.ticks_ms()
    _sqw_count += 1


def _two(value):
    return "%02d" % value


def start(rtc_dev):
    """Create a timestamped file and write the compatible CSV header."""
    global _path, _active, _last_sample, _sqw, _sqw_count, _sqw_seen
    _rtc.enable_1hz_sqw(rtc_dev)
    _sqw = Pin(2, Pin.IN, Pin.PULL_UP)
    _sqw.irq(trigger=Pin.IRQ_RISING, handler=_sqw_irq)
    _sqw_count = 0
    _sqw_seen = 0
    y, mo, d, h, mi, _ = _rtc.read_time(rtc_dev)
    _path = "%02d%02d%02d-%02d-%02d_OpenCTDKd.csv" % (y % 100, mo, d, h, mi)
    if _storage.exists(_path):
        raise OSError("recording file already exists: " + _path)
    _storage.append_csv(_path, _HEADER)
    _active = True
    _last_sample = 0
    print("Recording started:", _path)
    return _path


def stop():
    """End the current recording session without unmounting the SD card."""
    global _active, _sqw
    _active = False
    if _sqw is not None:
        _sqw.irq(handler=None)
        _sqw = None
    print("Recording stopped:", _path)


def active():
    return _active


def path():
    return _path


def clock_status():
    """Return whether a recent SQW edge has been received."""
    if _sqw_count == 0:
        return "waiting"
    age = time.ticks_diff(time.ticks_ms(), _sqw_ticks)
    return "locked" if age <= 1500 else "missing"


def _timestamp(rtc_dev, now_ms):
    global _sqw_seen
    if _sqw_count != _sqw_seen:
        _sqw_seen = _sqw_count
        print("SQW sync: pulse %d" % _sqw_seen)
    y, mo, d, h, mi, s = _rtc.read_time(rtc_dev)
    millis = time.ticks_diff(now_ms, _sqw_ticks) % 1000 if _sqw_count else 0
    return ("%04d/%02d/%02d" % (y, mo, d),
            "%02d:%02d:%02d.%03d" % (h, mi, s, millis))


def sample_if_due(rtc_dev, spectral_dev, pressure_dev, temp_dev, cond_dev, now_ms):
    """Take one row at the configured interval."""
    global _last_sample
    if not _active or (now_ms - _last_sample) < _interval_ms:
        return
    _last_sample = now_ms
    date_text, time_text = _timestamp(rtc_dev, now_ms)
    temp_c = _temp.read(temp_dev)
    pressure_mbar, _, depth_m = _pressure.read(pressure_dev)
    ec, tds, salinity, gravity = _cond.read(cond_dev, temp_c)
    channels = _spectral.read_channels(spectral_dev)
    values = [
        date_text, time_text,
        pressure_mbar, depth_m, temp_c, ec, tds, salinity, gravity,
    ]
    values.extend(channels.get(name, "") for name in _spectral.CHANNEL_NAMES)
    _storage.append_csv(_path, values)


def files():
    """Return CSV files in the SD root."""
    return [name for name in os.listdir("/sd") if name.lower().endswith(".csv")]


def read_file(name):
    _validate_name(name)
    return _storage.read_file(name)


def delete_file(name):
    _validate_name(name)
    if name == _path and _active:
        raise OSError("cannot delete the active recording")
    os.remove("/sd/" + name)


def _validate_name(name):
    if not name or name != name.split("/")[-1] or "\\" in name:
        raise ValueError("invalid file name")