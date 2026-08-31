# Atlas Scientific EZO Conductivity Notes

Atlas Scientific EZO circuits on an isolated carrier board support both UART (serial) and I2C communication modes, identifiable by their LED color (green for UART, blue for I2C).

## UART Mode

- **LED Indicator:** Blinking green
- **Wiring:** Uses separate TX (transmit) and RX (receive) lines
- **Best Use:** Easiest for microcontrollers like Arduino or direct USB/serial connection to a computer/Raspberry Pi
- **Pros/Cons:** Simple point-to-point communication, but requires dedicated pins and doesn't natively support multi-drop bus topologies easily without multiplexing

## I2C Mode

- **LED Indicator:** Solid/bright blue
- **Wiring:** Uses shared SDA (data) and SCL (clock) lines
- **Best Use:** Ideal for connecting multiple sensors to a single bus on microcontrollers or a Raspberry Pi
- **Pros/Cons:** Allows multiple EZO circuits on the exact same two pins using unique device addresses (default is 99), though addressing and command syntax differ slightly from UART

## Switching Modes

- **Default:** Circuits ship in UART mode
- **Via Software (when in UART):** Send the command `I2C,[address]` (e.g., `I2C,99`) over the serial connection to switch to I2C
- **Manually (Hardware):** Short the PGND (or PRB for RTD) pin to the TX pin with a jumper wire while powering on the device to toggle between modes

---

## Integration — Pico 2W on I2C0

EZO-EC default I2C address: **0x64** (100 decimal). No conflict with existing bus devices (`0x39`, `0x68`, `0x76`, `0x77`).

> **Note:** earlier project notes (`260817_ezo_ec_i2c_vs_uart.md`) incorrectly stated 0x62. Atlas Scientific datasheet and product page both confirm 100 (0x64). Code has been corrected.

### Wiring (I2C0 — shared with DS3231, AS7341, MS5837, TSYS01)

| Isolated Carrier Board | Pico 2W |
|------------------------|---------|
| VCC                    | 3.3V (pin 36) |
| GND                    | GND (pin 38) |
| SDA                    | GPIO4 (pin 6) |
| SCL                    | GPIO5 (pin 7) |

Probe connects to the PRB+ and PRB− screw terminals on the carrier board.

### Pre-flight: confirm I2C mode

LED on the EZO-EC must be **solid blue** before connecting to the Pico. If it is blinking green, the circuit is in UART mode. Three options to switch:

**Option A — Whitebox Labs I2C Toggler (easiest):**
1. Insert the EZO-EC into the toggler
2. Plug toggler into USB power
3. Press and hold the button for ~1 second; release when LED turns blue

**Option B — Hardware (manual, no computer needed):**
1. Power off the board
2. Disconnect TX and RX from any microcontroller
3. Short the **TX pin to the outer PRB pin** with a jumper wire — with pin labels read upright, this is the PRB pin on the right/outside edge of the board (the EZO-EC uses PRB, not PGND — PGND is on the EZO-pH)
4. Apply power; wait for LED to change from green → blue
5. Remove power, remove jumper
6. Wire for I2C

> Hardware switching resets the I2C address to the factory default (0x64 / 100).

**Option C — Software via UART terminal:**
1. Connect TX/RX to a USB–serial adapter or Arduino
2. Open serial monitor at 9600 baud with carriage return enabled
3. Confirm communication: send `I` — should return device info
4. Send `I2C,100` (or any address 1–127)
5. Device reboots; LED turns blue

### Files created

| File | Purpose |
|------|---------|
| `lib/ezo_ec.py` | EZO-EC I2C driver — null-terminated command write, status-byte response parse, temperature compensation (`T` command), reading (`R` command) returning `ec`, `tds`, `salinity`, `specific_gravity` |
| `lib/conductivity.py` | Clean module: `setup()`, `read(sensor, temperature_c)` → `(ec_us_cm, tds_ppm, salinity_psu, specific_gravity)` |
| `tests/conductivity_test.py` | 5-reading bringup test with I2C scan |
| `tests/conductivity_monitor.py` | 60-second continuous monitor at 1 reading/s |

### Capabilities

- **EC range:** 0.07–500,000 µS/cm
- **TDS:** derived from EC by the EZO firmware (configurable TDS factor)
- **Salinity:** PSU (practical salinity units), EZO firmware calculation
- **Specific gravity:** relative to pure water, EZO firmware calculation
- **Temperature compensation:** send `T,[°C]` before each `R` command; pass TSYS01 reading for accuracy
- **Calibration:** dry-point (`CAL,dry`), single-point (`CAL,low,[µS]`), two-point (`CAL,high,[µS]`) — all sendable over I2C from the MicroPython REPL

### Bringup result — 2026-08-27

I2C scan after integration: `0x39`, `0x64`, `0x68`, `0x76`, `0x77` — all five devices confirmed, no address conflicts.

Sensor initialised and returned 5 readings (`0.00 µS/cm`) with probe in air — expected behaviour per Atlas Scientific documentation.

**MicroPython fix:** `bytes.index(value, start)` with a start offset is not supported in MicroPython. The driver was updated to use a manual `for` loop to find the null terminator in the response buffer.