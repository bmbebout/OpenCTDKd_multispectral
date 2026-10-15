# EZO-RTD Integration, EC Compensation and ERR Recording

Date: 2026-10-14

Supersedes the open items in `261005_ezo_rtd_integration.md`.

## EZO-RTD bring-up

- Switched the EZO-RTD from UART to I2C over an FTDI TTL-232RG-**VIP**-WE cable
  (red wire is an *input* on the VIP variant, so the EZO was powered separately and
  the red wire tied to 3.3 V as the logic reference).
- Sent `C,0` (stop continuous output), then `I2C,102` at 9600 baud. The first
  `I2C,102` returned `*ER` while readings were streaming. LED is steady blue; scan
  now shows `0x66`.
- Wiring to the Pico: Vcc -> 3V3, GND -> GND, carrier `TX` = SDA -> GPIO4,
  carrier `RX` = SCL -> GPIO5.
- Green flash on the EZO-RTD LED in I2C mode means "taking reading" per the datasheet.

## Code

- `lib/ezo_rtd.py` - driver (address `0x66`, `R` takes 600 ms, forces Celsius scale).
  `start()` begins a conversion, `read()` collects it.
- `lib/temperature_rtd.py` - manager (`setup` / `read` / `start`), parallel to
  `lib/temperature.py` (TSYS01), which is unchanged.
- `lib/sensors.py` - `read_all()` shared by the dashboard and the recorder.
- `tests/temperature_rtd_test.py`, `tests/temperature_rtd_monitor.py`,
  `tests/sensors_test.py`; `scripts/deploy.sh` copies the new files.

## EC temperature compensation

- Compensation was already active (`T,<temp>` before each `R`) but used the TSYS01.
  It now uses the EZO-RTD reading. Verified on the EZO-EC with `T,?`.
- No fallback: if the RTD read fails, EC, TDS, salinity and specific gravity are `ERR`.

## ERR policy

- Any failed sensor read is recorded as `ERR` in its columns, never 0 or a substitute.
  The dashboard and OLED show `ERR` the same way.
- A sensor that fails setup at boot no longer stops the firmware. The RTC is still
  fatal (rows need a timestamp).
- CSV: `Temp` replaced by `Temp_TSYS01` and `Temp_RTD` (after Depth).
- Sensors are recorded as observed; no lag correction. They are sampled in
  sequence over about 1.5 s per row, timestamp taken at the start of the row.

## Lazy sensor loading and health

- `lib/sensors.py` `Sensor` wraps each I2C sensor: set up on first use, retried every 5 s
  while not ready, fully re-initialised after any failed read (a power-glitched sensor
  can otherwise return plausible but wrong data). Readiness is per sensor; EC is `ERR`
  while the RTD is not ready, but EC itself can be ready.
- The idle loop calls `sensors.maintain()` (every 5 s): retries sensors that are not
  ready and flags ready ones that vanish from an I2C scan. This runs with no dashboard
  connected, so sensors that start slowly come up during the idle period before the
  first reading. While recording, the sampling reads drive recovery instead.
- Transitions are logged once to `log.txt`: `sensor_ready`, `sensor_lost`,
  `sensor_unavailable`.
- Dashboard: "Sensor Health" section, a green/red indicator and last error per sensor.
  OLED: third rotating screen, `SENSORS` `PASS`/`FAIL` (added the missing `F` glyph).
- `spectral.read_channels` renamed `spectral.read` to match the other managers; each
  manager now exposes `ADDR`.

## Bugs found

- Right after a reset, a conversion left unread made the first `i` return the stale
  reading, failing RTD setup. `setup()` now retries until the reply identifies an RTD.
- `S,?` replies `?S,C`; the lowercase compare re-wrote the scale on every boot. Fixed.
- One EZO-EC "not responding" on a first verify was not diagnosed or reproduced; lazy
  retry would now recover from it.

## Open items

- Cold power-up is still untested on hardware (all tests were soft resets, sensors
  stayed powered). Lazy loading should handle slow-starting sensors; verify with a real
  power cycle.
- A wedged shared I2C bus (brownout, water ingress) would fail every I2C sensor; retries
  cannot clear it. Needs a bus-clear recovery (toggle SCL, re-create the I2C object).
- RTD reads about 0.8 C warmer than the TSYS01; compare in the same water bath.
- A row takes about 1.5 s (RTD read fresh each row), longer than the 1 s interval.
- RTC read failure still skips the row.
- Confirm the RTD green flash cadence (about 3 s observed) against our read schedule
  (the dashboard polls every 5 s; the idle bus scan every 5 s also touches the RTD address).
