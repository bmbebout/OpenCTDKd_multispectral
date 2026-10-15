# Session Summary - EZO-RTD, EC Compensation, ERR Recording, Lazy Sensors

Date: 2026-10-14

Technical detail is in `261014_ezo_rtd_ec_compensation.md`; this is the status at the pause.

## Done

- **EZO-RTD on I2C (0x66):** switched from UART over an FTDI TTL-232RG-VIP cable, wired
  to the Pico (Vcc 3V3, GND, TX=SDA GPIO4, RX=SCL GPIO5). Runs in parallel with the
  TSYS01 via `lib/ezo_rtd.py` and `lib/temperature_rtd.py`.
- **EC temperature compensation** now uses the RTD (was TSYS01), verified with `T,?`.
  No fallback: if the RTD fails, EC columns are `ERR`.
- **Both temperatures recorded:** CSV columns `Temp_TSYS01`, `Temp_RTD`. No lag correction.
- **ERR policy:** any failed sensor read records `ERR` (CSV, dashboard, OLED) via
  `lib/sensors.py` `read_all`, shared by the dashboard and the recorder.
- **Lazy sensor loading:** `Sensor` wrapper per I2C sensor, 5 s retry, full re-init after
  any failed read. Sensors missing at boot no longer stop the firmware (RTC still does).
  The idle loop runs `sensors.maintain()` so sensors come up with no dashboard connected.
- **Health display:** dashboard "Sensor Health" rows (ready dot + last error); OLED
  `SENSORS PASS/FAIL` screen. Ready/lost transitions are logged to `log.txt`.
- **Bugs fixed:** stale reading after reset broke RTD setup; RTD scale re-written every
  boot (`?S,C` case); `spectral.read_channels` renamed to `read` for consistency.

## Repository

Pushed to `origin/master`:

- `239f80b` EZO-RTD, RTD-based EC compensation, ERR recording
- `ca96c5d` Lazy sensor loading with health in the dashboard and OLED

The firmware on the Pico (COM4) matches `ca96c5d`.

## Verified on hardware

Bring-up and readings of both temperature sensors, compensation value on the EC, recorder
CSV rows with and without the RTD (`ERR` columns), dashboard status JSON, simulated sensor
failures and recovery (including a real RTD forced down and recovered by `maintain()`),
reboot from the earlier failing state, and idle running for 30 s without errors.

## Not yet verified

- Dashboard page and OLED third screen as seen by eye (the page is served at
  `http://192.168.4.1` on the `OpenCTDKd` network).
- Real cold power-up (all resets so far were soft; sensors stayed powered).
- A physically unplugged sensor, as opposed to the simulated failures.

## Next

1. Check the web UI and OLED; unplug and replug the RTD to watch it go red and recover.
2. Cold power-cycle test with serial capture.
3. Compare RTD and TSYS01 in one water bath (RTD reads about 0.8 C warmer in air).
4. I2C bus-clear recovery for a wedged shared bus.
5. Decide on the ~1.5 s per-row time versus the 1 s interval, and on RTC-failure rows
   (currently skipped).
6. Check the RTD green LED flash cadence (about 3 s seen) against the 5 s dashboard poll and
   5 s idle bus scan.

## Housekeeping

`log.txt` on the SD card holds `record_start` / `record_stop` lines from a test recording
whose CSV was deleted, and the sensor events from test runs.
