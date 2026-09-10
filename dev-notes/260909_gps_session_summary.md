# GPS Session Summary

Date: 2026-09-09

## Component

Added GY-GPS6MU2 / NEO-6M support over UART1 for startup positioning and UTC
clock synchronization.

- `lib/neo6m.py` parses RMC and GGA NMEA sentences.
- `lib/gps.py` owns UART setup, non-blocking snapshots, quality checks, RTC
  synchronization, and metadata formatting.
- `tests/gps_test.py` provides a hardware bring-up check.

## Wiring

- GPS TX -> Pico GPIO9 / UART1 RX
- GPS RX -> Pico GPIO8 / UART1 TX
- VCC -> 3V3 OUT
- GND -> GND
- UART speed: 9600 baud

## Behavior

GPS polling is non-blocking during idle/configuration mode. A usable fix requires
valid RMC and GGA data, at least four satellites, and HDOP no greater than 5.0.
When available at startup, GPS UTC synchronizes the DS3231 and is recorded with
signed RTC drift. Recording keeps the last GPS state and stops polling after it
starts.

Recording metadata includes GPS fix status, position, altitude, satellite count,
quality, UTC start time, and RTC source. UTC user events are written to `log.txt`.
If a good fix is unavailable, the existing RTC time is retained.

## Validation

The firmware was compiled and deployed to the Pico on COM4 during this session.
