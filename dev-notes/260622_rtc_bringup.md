# RTC Bringup & Project Scaffolding

**Date:** 2026-06-22  
**Hardware:** Raspberry Pi Pico 2W + Adafruit DS3231 (#3013)

---

## Wiring

| DS3231 | Pico 2W |
|--------|---------|
| VIN    | 3.3V (pin 36) |
| GND    | GND (pin 38) |
| SDA    | GPIO4 (pin 6) |
| SCL    | GPIO5 (pin 7) |

Adafruit DS3231 board has onboard pull-ups; no external resistors needed.

---

## What Was Done

### Hardware verified
- I2C scan confirmed DS3231 at `0x68`
- Temperature reading `26.75–27.0°C` (room temp, register reads working)
- Time set to system clock; tick confirmed across reads

### Files created

| File | Purpose |
|------|---------|
| `lib/ds3231.py` | DS3231 low-level I2C driver (`get_datetime`, `set_datetime`, `temperature`) |
| `lib/rtc.py` | Clean RTC module — public API: `setup()`, `read_time()`, `set_time()`, `read_temperature()` |
| `main.py` | Project entry point; `boot()` initialises hardware and prints RTC time, `idle()` is the state machine stub |
| `tests/rtc_test.py` | Interactive set/read utility (dev only, not deployed) |
| `scripts/dev_run.sh` | Mount local source on Pico and run `main.py` — no file copy needed |
| `scripts/deploy.sh` | Copy all project files to Pico filesystem for standalone boot |
| `scripts/monitor.sh` | Exec deployed `main.py` from Pico filesystem and stream output |

### Conventions established
- `lib/` — deployed modules; one file per hardware component
- `tests/` — per-component bringup scripts, run with `mpremote run`, never deployed
- `scripts/` — shell utilities for the dev workflow

---

## Dev Workflow

All commands from workspace root (`kdupro_openctd_integration_work/`):

```bash
# Fast edit-run loop (no copy needed)
bash OpenCTDKd_multispectral/scripts/dev_run.sh

# Deploy to Pico for standalone boot
bash OpenCTDKd_multispectral/scripts/deploy.sh

# Stream output from deployed Pico
bash OpenCTDKd_multispectral/scripts/monitor.sh
```

---

## Notes

- `mpremote run` does not pass stdin through Git Bash — interactive scripts must use `mpremote repl` or be driven via `mpremote exec`.
- DS3231 loses time if CR2032 is dead/absent; shows `2000-01-01 00:00:00` on first use.
- `deploy.sh` skips unchanged files (`Up to date:` message from mpremote).
