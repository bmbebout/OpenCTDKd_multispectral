"""Shared sensor sampling bringup test - prints one full read_all() snapshot per second.

Any sensor that fails to read shows as ERR; EC shows ERR whenever the RTD does.
To see the ERR path, unplug the EZO-RTD (and reset) before running.

Run:
    mpremote connect COM4 mount . run tests/sensors_test.py
"""

import time
import lib.sensors as sensors
import lib.spectral as spectral
import lib.pressure as pressure
import lib.temperature as temperature
import lib.temperature_rtd as temperature_rtd
import lib.conductivity as conductivity

_READS = 3


def _setup(module):
    try:
        return module.setup()
    except OSError as e:
        print("setup failed:", e)
        return None


def main():
    print("=== sensors.read_all test ===")
    spectral_dev = _setup(spectral)
    pressure_dev = _setup(pressure)
    temp_dev = _setup(temperature)
    rtd_dev = _setup(temperature_rtd)
    cond_dev = _setup(conductivity)

    for _ in range(_READS):
        start = time.ticks_ms()
        data = sensors.read_all(spectral_dev, pressure_dev, temp_dev, rtd_dev, cond_dev)
        elapsed = time.ticks_diff(time.ticks_ms(), start)
        spectrum = data.pop("spectral")
        print(data)
        print("  spectral:", spectrum)
        print("  read_all took %d ms" % elapsed)

    print("\nDone.")


main()
