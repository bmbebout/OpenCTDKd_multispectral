"""Sensor lifecycle and sampling shared by the dashboard and the CSV recorder.

Each sensor is wrapped in a Sensor that initialises lazily: it is set up on
first use, and after any failed read it is re-initialised, retrying every
_RETRY_MS until it works. A sensor that fails to read yields ERR in its place -
never zero or a substitute from another sensor - so internal errors stay
visible in the dashboard and recorded data.

Public API:
    ERR                                       marker for a failed value
    Sensor(label, module, addr)               lazily initialised sensor wrapper
    set_event_logger(fn)                      fn(message) receives ready/lost events
    read_all(spectral, pressure, temp, rtd, cond)  -> dict of readings
    maintain(sensors)                         idle-time retry and dropout check
    health(*sensors)                          -> {label: {"ready", "error"}}
    all_ready(*sensors)                       -> True when every sensor is ready
"""

import time
from machine import I2C, Pin
from lib.spectral import CHANNEL_NAMES

ERR = "ERR"

_RETRY_MS = const(5000)  # between setup attempts while a sensor is not ready
_SCAN_MS  = const(5000)  # between idle-time bus checks

_log_event = None
_i2c = None
_last_scan = None


def set_event_logger(fn):
    """Register fn(message) to receive sensor ready/lost events (e.g. for log.txt)."""
    global _log_event
    _log_event = fn


class Sensor:
    """A sensor that initialises lazily and re-initialises after any failed read.
    module provides setup() -> device and read(device, ...); addr is its I2C address."""

    def __init__(self, label, module, addr):
        self.label = label
        self.addr = addr
        self.error = ""
        self._module = module
        self._device = None
        self._ready = None  # None until the first attempt, so it counts as a change
        self._last_try = None

    @property
    def ready(self):
        return bool(self._ready)

    def attempt(self, force=False):
        """Set the sensor up if it is not ready, at most once per _RETRY_MS unless forced."""
        if self._ready:
            return
        now = time.ticks_ms()
        if not force and self._last_try is not None \
                and time.ticks_diff(now, self._last_try) < _RETRY_MS:
            return
        self._last_try = now
        try:
            self._device = self._module.setup()
        except Exception as e:
            self.fail(e)
        else:
            self._set(True)

    def fail(self, error):
        """Mark the sensor not ready so the next use re-initialises it."""
        self._device = None
        self._set(False, error)

    def call(self, name, *args):
        """Run module function `name` on the device, initialising it first if needed.
        Raises OSError if the sensor is not ready; any failure marks it not ready."""
        self.attempt()
        if not self._ready:
            raise OSError("not ready: " + self.error)
        try:
            return getattr(self._module, name)(self._device, *args)
        except Exception as e:
            self.fail(e)
            raise

    def read(self, *args):
        return self.call("read", *args)

    def _set(self, ready, error=None):
        """Record a state change and report it once."""
        was = self._ready
        self._ready = ready
        self.error = "" if ready else str(error)
        if ready == was:
            return
        if ready:
            event = "sensor_ready sensor=%s" % self.label
        elif was:
            event = "sensor_lost sensor=%s error=%s" % (self.label, self.error)
        else:
            event = "sensor_unavailable sensor=%s error=%s" % (self.label, self.error)
        print(event)
        if _log_event is not None:
            _log_event(event)


def _bus():
    """Return the shared I2C0 bus object, creating it on first use."""
    global _i2c
    if _i2c is None:
        _i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100_000)
    return _i2c


def maintain(sensors):
    """Idle-time upkeep: retry sensors that are not ready, and mark ready sensors
    that have disappeared from the bus. Throttled, so it is cheap to call every loop."""
    global _last_scan
    now = time.ticks_ms()
    if _last_scan is not None and time.ticks_diff(now, _last_scan) < _SCAN_MS:
        return
    _last_scan = now
    present = None
    for sensor in sensors:
        if not sensor.ready:
            sensor.attempt()
            continue
        if present is None:
            try:
                present = _bus().scan()
            except OSError:
                return
        if sensor.addr not in present:
            sensor.fail(OSError("not found on I2C bus"))


def health(*sensors):
    """Return {label: {"ready": bool, "error": str}} for the dashboard."""
    return {s.label: {"ready": s.ready, "error": s.error} for s in sensors}


def all_ready(*sensors):
    return all(s.ready for s in sensors)


def _guard(label, default, fn, *args):
    """Return fn(*args), or default (after a serial message) if the read fails."""
    try:
        return fn(*args)
    except Exception as e:
        print("%s read error: %s" % (label, e))
        return default


def read_all(spectral_dev, pressure_dev, temp_dev, rtd_dev, cond_dev):
    """Read every sensor once. Keys: temperature_c (TSYS01), rtd_c (EZO-RTD),
    pressure_mbar, depth_m, ec_us_cm, tds_ppm, salinity_psu, specific_gravity,
    and spectral (dict of channel name -> counts). Failed values are ERR.
    EC is ERR whenever the RTD temperature needed to compensate it is ERR."""
    # The RTD converts in the background while the faster sensors are read
    if rtd_dev.ready:
        _guard(rtd_dev.label, None, rtd_dev.call, "start")

    channels = _guard(spectral_dev.label, {}, spectral_dev.read)
    pressure_mbar, _, depth_m = _guard(pressure_dev.label, (ERR, ERR, ERR), pressure_dev.read)
    tsys_c = _guard(temp_dev.label, ERR, temp_dev.read)
    rtd_c = _guard(rtd_dev.label, ERR, rtd_dev.read)

    if rtd_c == ERR:
        ec = tds = salinity = gravity = ERR
    else:
        ec, tds, salinity, gravity = _guard(cond_dev.label, (ERR,) * 4, cond_dev.read, rtd_c)

    return {
        "temperature_c": tsys_c,
        "rtd_c": rtd_c,
        "pressure_mbar": pressure_mbar,
        "depth_m": depth_m,
        "ec_us_cm": ec,
        "tds_ppm": tds,
        "salinity_psu": salinity,
        "specific_gravity": gravity,
        "spectral": {name: channels.get(name, ERR) for name in CHANNEL_NAMES},
    }
