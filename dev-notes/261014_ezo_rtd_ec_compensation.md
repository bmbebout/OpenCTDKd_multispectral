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
- A sensor that fails setup at boot no longer stops the firmware; it stays `None`
  and its columns record `ERR`. The RTC is still fatal (rows need a timestamp).
- CSV: `Temp` replaced by `Temp_TSYS01` and `Temp_RTD` (after Depth).
- Sensors are recorded as observed; no lag correction. They are sampled in
  sequence over about 1.5 s per row, timestamp taken at the start of the row.

## Bugs found

- Right after a reset, a conversion left unread made the first `i` return the stale
  reading, failing RTD setup. `setup()` now retries until the reply identifies an RTD.
- `S,?` replies `?S,C`; the lowercase compare re-wrote the scale on every boot. Fixed.
- One EZO-EC "not responding" on a first verify was not diagnosed or reproduced.

## Open items

- Cold power-up is untested (all tests were soft resets, sensors stayed powered).
  `setup()` scans once and gives up, so a slow-starting sensor would record `ERR` for
  the whole session. Consider a startup retry window and test with a real power cycle.
- RTD reads about 0.8 C warmer than the TSYS01; compare in the same water bath.
- A row takes about 1.5 s (RTD read fresh each row), longer than the 1 s interval.
- RTC read failure still skips the row.
- Confirm the RTD green flash cadence (about 3 s observed) against our read schedule
  (the dashboard polls every 5 s).
