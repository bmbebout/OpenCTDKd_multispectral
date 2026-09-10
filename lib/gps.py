"""GPS module — GY-GPS6MU2 on UART1 (TX=GPIO8, RX=GPIO9).

Public API:
    setup()                         -> NEO6M receiver
    read(receiver)                  -> latest GPS snapshot
    sync_rtc(receiver, rtc_device) -> True if the RTC was set from GPS UTC
    metadata(receiver, rtc_source)  -> CSV preamble key/value pairs
"""

import time as _time
from machine import UART, Pin
import lib.rtc as _rtc
import lib.storage as _storage
from lib.neo6m import NEO6M

_UART_ID = 1
_TX = 8
_RX = 9
_BAUD = 9600


def setup():
    """Initialise UART1 and return a GPS receiver instance."""
    uart = UART(_UART_ID, baudrate=_BAUD, tx=Pin(_TX), rx=Pin(_RX))
    receiver = NEO6M(uart)
    print("GPS:   GY-GPS6MU2 ready on UART1")
    return receiver


def read(receiver, poll=True):
    """Return the latest position, optionally polling the receiver first."""
    if receiver is None:
        return _empty_snapshot()
    if poll:
        receiver.update()
    return receiver.snapshot(poll=poll)


def poll(receiver, rtc_device):
    """Process GPS input and perform the one-time startup RTC synchronization."""
    if receiver is None:
        return
    receiver.update()
    if not quality_good(receiver) or receiver._utc is None or getattr(receiver, "_rtc_synced", False):
        return
    gps_time = receiver._utc
    rtc_time = _rtc.read_time(rtc_device)
    drift_seconds = _time_seconds(gps_time) - _time_seconds(rtc_time)
    try:
        _storage.append_log(
            "gps_first_good_fix quality=%s gps_time=%s rtc_time=%s drift_seconds=%d" %
            (quality_description(receiver), _format_time(gps_time),
             _format_time(rtc_time), drift_seconds),
            _format_time(gps_time))
    except OSError as e:
        print("GPS log error:", e)
    _rtc.set_time(rtc_device, *gps_time)
    receiver._rtc_synced = True
    print("RTC:   synchronized from GPS UTC (drift %d s)" % drift_seconds)


def sync_rtc(receiver, rtc_device, timeout_ms=10000):
    """Compatibility helper: wait briefly, then perform the normal sync."""
    if receiver is None or not receiver.wait_for_fix(timeout_ms):
        return False
    poll(receiver, rtc_device)
    return getattr(receiver, "_rtc_synced", False)


def metadata(receiver, rtc_source):
    """Return metadata values for the beginning of a recording file."""
    snapshot = read(receiver, poll=False)
    return {
        "gps_fix": "1" if snapshot["fix"] else "0",
        "gps_status": status(receiver),
        "latitude": _format_value(snapshot["latitude"]),
        "longitude": _format_value(snapshot["longitude"]),
        "gps_quality": quality_description(receiver),
        "altitude_m": _format_value(snapshot["altitude_m"]),
        "satellites": str(snapshot["satellites"]),
        "rtc_source": "gps" if getattr(receiver, "_rtc_synced", False) else rtc_source,
    }


def status(receiver):
    """Return a concise user-facing GPS state."""
    if receiver is None:
        return "unavailable"
    if quality_good(receiver):
        return "good_fix"
    if receiver._fix:
        return "fix_pending_quality"
    return "no_fix" if receiver._seen_sentence else "searching"


def quality_good(receiver):
    return (receiver is not None and receiver._fix and
            receiver._satellites >= 4 and receiver._hdop is not None and
            receiver._hdop <= 5.0)


def quality_description(receiver):
    if receiver is None:
        return "unavailable"
    if not receiver._fix:
        return "no valid fix"
    if receiver._hdop is None:
        return "fix pending HDOP"
    description = "GPS fix; satellites=%d; HDOP=%.1f" % (receiver._satellites, receiver._hdop)
    if quality_good(receiver):
        return "good (%s)" % description
    return "fix pending quality (%s)" % description


def rtc_source(receiver, fallback):
    return "gps" if receiver is not None and getattr(receiver, "_rtc_synced", False) else fallback


def ready(receiver):
    """Return true only after a good GPS fix synchronized the RTC."""
    return quality_good(receiver) and getattr(receiver, "_rtc_synced", False)


def _empty_snapshot():
    return {
        "fix": False,
        "latitude": None,
        "longitude": None,
        "altitude_m": None,
        "satellites": 0,
        "quality_code": 0,
        "hdop": None,
        "utc": None,
    }


def _format_value(value):
    return "" if value is None else "%.7f" % value


def _format_time(value):
    return "%04d-%02d-%02dT%02d:%02d:%02d" % value


def _time_seconds(value):
    return _time.mktime(value + (0, 0, 0))