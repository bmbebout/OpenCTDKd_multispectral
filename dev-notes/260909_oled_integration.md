# OLED Integration

The firmware supports a 128x32 SSD1306-compatible I2C OLED at address `0x3C`.
The display shares I2C0 with the existing RTC and sensors.

| OLED pin | Pico 2W | Physical pin |
|---|---|---|
| VCC | 3V3 OUT | 36 |
| GND | GND | 38 |
| SDA | GPIO4 / I2C0 SDA | 6 |
| SCL | GPIO5 / I2C0 SCL | 7 |

The module must be 3.3 V logic compatible. If the board uses address `0x3D`
instead of `0x3C`, update `_ADDR` in `lib/oled.py`. A 128x32 pixel size alone
does not identify the controller, so this integration assumes SSD1306.

The display rotates screens every two seconds:

- Screen 0: `READY` or `NOT RDY`, followed by `LINES:N`, where N is the number
	of successfully written sensor rows since boot.
- Screen 1: `CLEAR:<raw count>` and `T:<degrees>C`; changing values are
	right-aligned for easier visual comparison.

`READY` requires a good GPS fix, RTC synchronization, and an available SD card.
The Clear-channel value is the raw AS7341 reading, useful for spotting
clipping. The line count is not reset when a new recording starts.