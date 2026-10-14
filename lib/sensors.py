"""Sensor sampling shared by the dashboard and the CSV recorder.

A sensor that fails to read yields ERR in its place - never zero or a
substitute from another sensor - so internal errors stay visible in both the
dashboard and the recorded data.

Public API:
    ERR                                                     marker for a failed value
    read_all(spectral, pressure, temp, rtd, cond)           -> dict of readings
"""

import lib.spectral as _spectral
import lib.pressure as _pressure
import lib.temperature as _temp
import lib.temperature_rtd as _rtd
import lib.conductivity as _cond

ERR = "ERR"


def _guard(label, default, fn, *args):
    """Return fn(*args), or default (after a serial message) if the read fails.
    A sensor that failed setup is None and reads as a failure."""
    if args and args[0] is None:
        print("%s read error: sensor not initialised" % label)
        return default
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
    _rtd.start(rtd_dev)

    channels = _guard("Spectral", {}, _spectral.read_channels, spectral_dev)
    pressure_mbar, _, depth_m = _guard("Pressure", (ERR, ERR, ERR), _pressure.read, pressure_dev)
    tsys_c = _guard("TSYS01", ERR, _temp.read, temp_dev)
    rtd_c = _guard("EZO-RTD", ERR, _rtd.read, rtd_dev)

    if rtd_c == ERR:
        ec = tds = salinity = gravity = ERR
    else:
        ec, tds, salinity, gravity = _guard("EZO-EC", (ERR,) * 4, _cond.read, cond_dev, rtd_c)

    return {
        "temperature_c": tsys_c,
        "rtd_c": rtd_c,
        "pressure_mbar": pressure_mbar,
        "depth_m": depth_m,
        "ec_us_cm": ec,
        "tds_ppm": tds,
        "salinity_psu": salinity,
        "specific_gravity": gravity,
        "spectral": {name: channels.get(name, ERR) for name in _spectral.CHANNEL_NAMES},
    }
