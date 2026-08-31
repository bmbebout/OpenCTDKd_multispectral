# Web Server and Data Recording

**Date:** 2026-08-31
**Hardware:** Raspberry Pi Pico 2W with DS3231 RTC, SD card, AS7341, MS5837, TSYS01, and EZO-EC

## Progress

The Pico now starts a WiFi access point and serves a browser dashboard while remaining available during data recording.

- AP SSID: `OpenCTDKd`
- AP password: `M$cience`
- Dashboard: `http://192.168.4.1`
- HTTP server uses raw MicroPython sockets with no external web dependency.
- Dashboard displays RTC time and current sensor readings.
- Status data is available at `GET /api/status`.
- JavaScript reports browser and API errors in the page for mobile debugging.

## Data Recording

Selecting **Start Data Recording** creates a new file on the SD card using:

```text
YYMMDD-HH-MM_OpenCTDKd.csv
```

The file receives a legacy-compatible comma-separated header and approximately one sensor row per second. Rows include date, time, pressure, depth, temperature, conductivity, TDS, salinity, specific gravity, and all ten AS7341 spectral channels.

The dashboard remains available during recording. **Stop Recording** ends sampling while leaving the CSV file on the card.

## SD Card File Operations

The dashboard provides:

- List available CSV files: `GET /api/files`
- Download a file: `GET /api/download?name=...`
- Delete a file: `GET /api/delete?name=...`

Downloads include a `Content-Disposition` filename. Active recordings cannot be deleted, and file names are restricted to the SD root.

## RTC and SQW

The DS3231 can be synchronized from the computer with a one-shot `mpremote` command. GPS time integration is deferred until the GPS module is integrated.

The DS3231 1 Hz `SQW` output is configured when recording starts and captured on Pico GPIO2 (physical pin 4). When wired and functioning, CSV timestamps include milliseconds and the dashboard reports `SQW locked`. `waiting` indicates that no SQW rising edge has been detected.

## Deployment

From the workspace root:

```bash
bash OpenCTDKd_multispectral/scripts/deploy.sh COM4
```

The deployment script releases stale `mpremote` processes, copies all firmware modules, and resets the Pico. `monitor.sh` can attach to the serial console for diagnostics.
