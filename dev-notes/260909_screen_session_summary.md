# OLED Screen Session Summary

Date: 2026-09-09

## Component

Added a 128x32 SSD1306 I2C OLED status display on the shared I2C0 bus.

- `lib/oled.py` initializes the display, renders the page-addressed framebuffer,
  and treats display errors as non-fatal.
- `lib/webserver.py` supplies readiness, line count, Clear, and temperature data.
- `lib/recording.py` shares the latest sensor values with the idle OLED refresh.

## Wiring

- OLED SDA -> Pico GPIO4 / I2C0 SDA
- OLED SCL -> Pico GPIO5 / I2C0 SCL
- VCC -> 3V3 OUT
- GND -> GND
- Address: `0x3C`

## Display behavior

The display rotates every two seconds:

- Screen 0: `READY` or `NOT RDY`, then `LINES:N`
- Screen 1: `CLEAR:<raw AS7341 count>`, then `T:<degrees>C`

The changing values are right-aligned to make hand-over-sensor changes easier
to see. Screen 1 uses the latest dashboard readings before recording begins and
recording readings afterward. Large I2C framebuffer writes are chunked to avoid
OLED timeouts.

## Validation

The firmware was compiled and deployed to the Pico on COM4 during this session.
