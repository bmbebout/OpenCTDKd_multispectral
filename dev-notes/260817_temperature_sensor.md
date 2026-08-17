# TSYS01 Temperature Sensor Integration

**Date:** 2026-08-17

---

## Hardware

Blue Robotics Celsius Fast-Response Temperature Sensor (TSYS01, I2C addr `0x77`)

### Wiring (I2C0 — shared with DS3231, AS7341, MS5837)

| Celsius cable | Pico 2W |
|---------------|---------|
| Red (power)   | 3.3V (pin 36) |
| Black (GND)   | GND (pin 38) |
| White (SDA)   | GPIO4 (pin 6) |
| Green (SCL)   | GPIO5 (pin 7) |

I2C scan after integration: `0x39`, `0x68`, `0x76`, `0x77` — all four I2C devices confirmed. No address conflicts.

---

## Files created

| File | Purpose |
|------|---------|
| `lib/tsys01.py` | TSYS01 I2C driver — reset, 5-word PROM read, single conversion (0x48), 3-byte ADC read, 4th-order polynomial calibration; `.temperature` attribute (°C) |
| `lib/temperature.py` | Clean module: `setup()`, `read(sensor)` → `float` °C |
| `tests/temperature_test.py` | 5-reading bringup test with I2C scan |
| `tests/temperature_monitor.py` | 60-second continuous monitor at 1 reading/s |

Ported from Blue Robotics [tsys01-python](https://github.com/bluerobotics/tsys01-python) (MIT). Driver rewritten for MicroPython I2C; upstream library uses `smbus`.

---

## Capabilities

- **Temperature range:** −40 to +125°C, rated accuracy ±0.1°C (0–60°C)
- **Resolution:** ~0.01°C at 24-bit ADC with factory PROM calibration
- **Conversion time:** ~12 ms per reading (datasheet max 9.04 ms; driver adds margin)
- **Calibration:** 5 factory PROM words (k0–k4 at 0xAA–0xA2); loaded once at `setup()`, no re-read needed
- **Formula:** 4th-order polynomial per TSYS01 datasheet Table 2 — single pass, no second-order correction required

---

## Notes

- TSYS01 is the primary water temperature sensor for the data log. The MS5837 also has an internal temperature sensor but it is used only for pressure compensation.
- PROM addresses read high-to-low (0xAA → 0xA2); array index 0 = k0, index 4 = k4 — matches formula coefficient order directly.
