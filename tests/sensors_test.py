"""Sensor lifecycle bringup test - prints sensor health and read_all() snapshots.

Any sensor that fails to read shows as ERR; EC shows ERR whenever the RTD does.
To see the not-ready path, unplug a sensor before running (power it down first).

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


def main():
    print("=== sensors test ===")
    spectral_dev = sensors.Sensor("AS7341", spectral, spectral.ADDR)
    pressure_dev = sensors.Sensor("MS5837", pressure, pressure.ADDR)
    temp_dev = sensors.Sensor("TSYS01", temperature, temperature.ADDR)
    rtd_dev = sensors.Sensor("EZO-RTD", temperature_rtd, temperature_rtd.ADDR)
    cond_dev = sensors.Sensor("EZO-EC", conductivity, conductivity.ADDR)
    devs = (spectral_dev, pressure_dev, temp_dev, rtd_dev, cond_dev)

    for dev in devs:
        dev.attempt(force=True)
    print("health:", sensors.health(*devs))

    for _ in range(_READS):
        start = time.ticks_ms()
        data = sensors.read_all(*devs)
        elapsed = time.ticks_diff(time.ticks_ms(), start)
        spectrum = data.pop("spectral")
        print(data)
        print("  spectral:", spectrum)
        print("  read_all took %d ms" % elapsed)

    print("all ready:", sensors.all_ready(*devs))
    print("\nDone.")


main()
