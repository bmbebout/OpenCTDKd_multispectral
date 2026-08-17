# MS5837-30BA Pressure and Depth Sensor Integration

**Date:** 2026-08-17

---

## Hardware

Blue Robotics Bar30 High-Resolution 300m Depth/Pressure Sensor (MS5837-30BA, I2C addr `0x76`)

### Wiring (I2C0 — shared with DS3231, AS7341)

| Celsius cable | Pico 2W |
|---------------|---------|
| Red (power)   | 3.3V (pin 36) |
| Black (GND)   | GND (pin 38) |
| White (SDA)   | GPIO4 (pin 6) |
| Green (SCL)   | GPIO5 (pin 7) |

I2C scan after integration: `0x39`, `0x68`, `0x76` — all three devices confirmed.

---

## Files created

| File | Purpose |
|------|---------|
| `lib/ms5837.py` | MS5837-30BA I2C driver — PROM CRC verify, D1/D2 ADC conversion, 30BA second-order compensation formula; `.pressure` (mbar), `.temperature` (°C), `.depth(density)` |
| `lib/pressure.py` | Clean module: `setup()`, `read(sensor, density)` → `(pressure_mbar, temperature_c, depth_m)`; re-exports `DENSITY_FRESHWATER=997`, `DENSITY_SALTWATER=1029` |
| `tests/pressure_test.py` | 5-reading bringup test; prints `pressure_mbar`, `temperature_c`, `depth_m` |
| `tests/pressure_monitor.py` | 60-second continuous monitor at 1 reading/s (deadline loop with `ticks_ms`) |

Ported from Blue Robotics [ms5837-python](https://github.com/bluerobotics/ms5837-python) (MIT). The upstream library uses `smbus` (Linux only); the driver was rewritten from scratch for MicroPython I2C.

---

## Capabilities

- **Pressure:** 0–30 bar, ±2 mbar resolution after second-order compensation
- **Temperature:** onboard sensor used only for pressure compensation (use TSYS01 for calibrated water temperature)
- **Depth:** derived from pressure via `depth = (P_mbar × 100 − 101300) / (density × 9.80665)`; caller selects freshwater or saltwater density
- **OSR selection:** `OSR_256` (fastest, ~1 ms) through `OSR_8192` (highest accuracy, ~21 ms); default `OSR_8192`
- **PROM CRC:** checked on init; `OSError` raised if CRC fails

---

## Notes

- Large pressure excursions observed during the 60 s monitor run — confirmed as intentional; sensor was manually pressurised to simulate depth changes. Readings tracked the applied pressure correctly.
- MS5837 temperature attribute is not used in the boot output or data log; the TSYS01 is the dedicated water temperature sensor.
