# GPS Integration

## Hardware

The GY-GPS6MU2 is a NEO-6M-compatible UART GPS breakout. The project uses
UART1 so it does not conflict with the shared I2C0 bus, SPI0 SD card, or the
DS3231 SQW input on GPIO2.

| GPS pin | Pico 2W | Physical pin |
|---|---|---|
| VCC | 3V3 OUT | 36 |
| GND | GND | 38 |
| TX | GPIO9 / UART1 RX | 12 |
| RX | GPIO8 / UART1 TX | 11 |

Use 3.3 V logic. Some GY-GPS6MU2 breakout revisions accept 5 V on VCC, but
the Pico GPIOs must not receive 5 V signals; use the board documentation if a
different power arrangement is required.

The receiver normally emits NMEA at 9600 baud. An antenna and clear view of
the sky are required for a fix; a first fix can take longer after transport or
cold start.

## Firmware

- `lib/neo6m.py` parses RMC and GGA NMEA sentences.
- `lib/gps.py` owns UART setup, snapshots, RTC synchronization, and metadata.
- `tests/gps_test.py` waits for and prints a GPS fix.

At boot, GPS acquisition is non-blocking. The dashboard reports `searching`,
`no_fix`, `fix`, or `unavailable`, so the user can choose when to start a
recording. The first good startup fix is written to `log.txt` with human-readable
GPS quality, GPS UTC, the pre-synchronization RTC UTC, and signed drift in
seconds; the DS3231 is then set from GPS UTC. A good fix requires a valid RMC
position, a valid GGA fix, at least 4 satellites, and HDOP no greater than 5.0.
If no good fix is available, the existing RTC time is retained and the logger
continues to start.

Once recording starts, GPS input is no longer polled. The last known GPS state
is retained for the recording preamble. User actions are added to `log.txt` as
UTC events, including `record_start` and `record_stop`.

All device timestamps are treated as UTC. GPS provides UTC directly, and the
DS3231 is synchronized to UTC when a valid startup fix is obtained.

## CSV metadata convention

Each new recording begins with comment-prefixed key/value lines, followed by
the existing CSV header and data rows:

```text
# metadata_version=1
# start_time=2026-09-09T12:34:56
# gps_fix=1
# latitude=49.1234567
# longitude=-123.1234567
# gps_quality=good (GPS fix; satellites=8; HDOP=1.2)
# altitude_m=12.3000000
# satellites=8
# rtc_source=gps
Date,Time,Pressure,...
```

Lines beginning with `#` are metadata and can be skipped by CSV readers. The
first non-comment line remains the data header, preserving the existing data
column layout.