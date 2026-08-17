# SD Card and AS7341 Spectral Sensor Integration

**Date:** 2026-07-20

---

## SD Card Reader (SPI)

**Hardware:** Micro SD/SDHC TF Card Adapter Module with 3.3V level conversion

### Wiring (SPI0)

| SD module | Pico 2W |
|-----------|---------|
| 3V3 | 3.3V (pin 36) |
| GND | GND (pin 38) |
| MISO | GPIO16 (pin 21) |
| CS | GPIO17 (pin 22) |
| SCK | GPIO18 (pin 24) |
| MOSI | GPIO19 (pin 25) |

Note: module VCC is labelled **3V3** — 3.3V input only (internal level converter powered from 3.3V).

### Files created

| File | Purpose |
|------|---------|
| `lib/sdcard.py` | SPI block device driver — full SD init sequence (CMD0/CMD8/ACMD41/CMD58), SDSC + SDHC, implements `readblocks` / `writeblocks` / `ioctl` for `os.VfsFat` |
| `lib/storage.py` | Clean module: `setup()` mounts at `/sd`; `append_csv(path, values)`, `read_file(path)`, `exists(path)` |
| `tests/sdcard_test.py` | Bringup test: writes CSV header + 3 rows, reads back, verifies line count |

### Notes
- `CMD0 timeout` on first attempt — traced to incorrect wiring; resolved by re-seating the breakout board.
- `from lib.sdcard import SDCard` required inside `storage.py` to match the project module path convention (not bare `from sdcard import ...`).

---

## AS7341 10-Channel Spectral Sensor (I2C)

**Hardware:** Adafruit AS7341 breakout (I2C addr 0x39)

### Wiring (I2C0 — shared with DS3231 RTC)

| AS7341 | Pico 2W |
|--------|---------|
| VIN | 3.3V (pin 36) |
| GND | GND (pin 38) |
| SDA | GPIO4 (pin 6) |
| SCL | GPIO5 (pin 7) |

Both devices confirmed on I2C scan: `0x39` (AS7341), `0x68` (DS3231).

### Files created

| File | Purpose |
|------|---------|
| `lib/as7341.py` | I2C driver — WHOAMI check, power-on init, two-pass SMUX measurement, returns 10-channel dict |
| `lib/spectral.py` | Clean module: `setup()`, `read_channels(sensor)`, `CHANNEL_NAMES` list |
| `tests/spectral_test.py` | Bringup test: I2C scan + prints all 10 raw counts in a table |

### SMUX design note
The AS7341 has 10 photodiodes but only 6 ADC channels. Reading all 10 channels requires two passes with different SMUX configurations:
- **Pass 1** (`_SMUX_F1_F4`): ADC0-3 = F1–F4, ADC4 = Clear, ADC5 = NIR
- **Pass 2** (`_SMUX_F5_F8`): ADC0-3 = F5–F8, ADC4 = Clear, ADC5 = NIR

SMUX byte values derived from Adafruit CircuitPython AS7341 library (MIT). Default timing: ATIME=100, ASTEP=500, GAIN=128× ≈ 141 ms per pass.

---

## Boot sequence after both integrations

```
OpenCTDKd booting...
RTC:   2026-07-20  17:20:59
Temp:  27.5 C
SD:   mounted at /sd
Spectral: AS7341 ready
System ready. (idle)
```

## TODO
- Refactor I2C initialisation to use a single shared `I2C(0, ...)` instance across `rtc.py` and `spectral.py` once all I2C sensors are on the bus.
