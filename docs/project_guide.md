# OpenCTDKd Multispectral — Project Guide

A MicroPython datalogger for underwater multispectral light and CTD sensing,
running on the Raspberry Pi Pico 2W.

Combines the sensor suite of two prior instruments:
- **kdupro** — AS7341 multispectral light sensor, MONOCLE-compatible metadata
- **OpenCTD** — conductivity, temperature, and depth sensing

---

## Target Hardware

| Component | Part | Notes |
|---|---|---|
| Microcontroller | Raspberry Pi Pico 2W (RP2350) | MicroPython v1.28.0 |
| Multispectral light | Adafruit AS7341 10-channel | I2C, addr 0x39 |
| Pressure / depth | Blue Robotics Bar30 (MS5837-30BA) | I2C, addr 0x76, 30 bar / ~300m |
| Temperature | Blue Robotics Celsius Fast-Response (TSYS01) | I2C, addr 0x77, ±0.1°C |
| Conductivity | Atlas Scientific EZO-EC | UART 9600 baud |
| Real-time clock | DS3231 (Adafruit #3013 recommended) | I2C, addr 0x68, ±2 ppm TCXO, CR2032 onboard |
| Storage | MicroSD card module | SPI |
| Status indicator | RGB LED (external) | 3 GPIO pins, common cathode |
| Power | LiPo battery | Size/capacity TBD |
| Connectivity | USB (config/download) + WiFi (NTP only) | |

---

## Sensor Protocols Summary

| Bus | Devices |
|---|---|
| I2C | AS7341 (0x39), Bar30 MS5837-30BA (0x76), Celsius TSYS01 (0x77), DS3231 RTC (0x68) |
| UART | Atlas EZO-EC |
| SPI | SD card |
| WiFi | NTP time sync only (when USB-connected) |

All four I2C devices have distinct addresses and share one I2C bus.

---

## Recommended Pin Assignments (Pico 2W)

| Function | GPIO | Physical Pin | Notes |
|---|---|---|---|
| UART0 TX → EZO-EC RX | GPIO0 | 1 | Atlas EZO-EC |
| UART0 RX ← EZO-EC TX | GPIO1 | 2 | Atlas EZO-EC |
| I2C0 SDA | GPIO4 | 6 | AS7341, Bar30, Celsius, DS3231 |
| I2C0 SCL | GPIO5 | 7 | AS7341, Bar30, Celsius, DS3231 |
| RGB LED — Red | GPIO10 | 14 | Active high |
| RGB LED — Green | GPIO11 | 15 | Active high |
| RGB LED — Blue | GPIO12 | 16 | Active high |
| SPI0 MISO | GPIO16 | 21 | SD card |
| SPI0 CS (SD) | GPIO17 | 22 | SD card chip select |
| SPI0 SCK | GPIO18 | 24 | SD card |
| SPI0 MOSI | GPIO19 | 25 | SD card |
| 3.3V power | 3V3 OUT | 36 | All sensors |
| GND | GND | 38 | All sensors |

> **Pico 2W onboard LED** is controlled via the CYW43 WiFi chip, not a GPIO
> pin. In MicroPython: `import network; wlan = network.WLAN(); led = Pin('LED', Pin.OUT)`.

---

## Sensor Details

### AS7341 — 10-Channel Multispectral Light
- **Interface**: I2C (STEMMA QT / 4-pin JST SH)
- **Channels**: F1 415nm, F2 445nm, F3 480nm, F4 515nm, F5 555nm, F6 590nm,
  F7 630nm, F8 680nm, Clear, Near-IR
- **Config from kdupro**: ATIME=100, ASTEP=500, GAIN=128x
- **MicroPython library**: community port of Adafruit AS7341 driver (TBD — evaluate
  [adafruit/Adafruit_CircuitPython_AS7341](https://github.com/adafruit/Adafruit_CircuitPython_AS7341)
  vs a pure MicroPython port)
- **Reading strategy**: non-blocking startReading + polling (inherited from kdupro)

### MS5837-30BA — Pressure / Depth (Blue Robotics Bar30)
- **Interface**: I2C, address 0x76
- **Range**: 0–30 bar (~0–300m water depth)
- **Resolution**: configurable oversampling; use OSR 8192 (highest) for best accuracy
- **Outputs**: pressure (mbar), temperature (°C) — temp is less accurate than TSYS01
- **MicroPython library**: port available at
  [bluerobotics/ms5837-python](https://github.com/bluerobotics/ms5837-python)
  (needs adaptation from CPython to MicroPython)
- **Wiring note**: White = SDA, Green = SCL (Blue Robotics cable convention)

### TSYS01 — Temperature (Blue Robotics Celsius Fast-Response)
- **Interface**: I2C, address 0x77
- **Accuracy**: ±0.1°C
- **Response time**: ~1s (0.5 m/s flow), ~2s still water
- **MicroPython library**: community ports available; relatively simple protocol
  (reset, read calibration coefficients, trigger conversion, read result)
- **Wiring**: JST GH connector (same Blue Robotics cable convention)

### Atlas Scientific EZO-EC — Conductivity
- **Interface**: UART at 9600 baud (default); can also do I2C if address jumper set
- **Init sequence** (inherited from OpenCTD):
  1. Send `i\r` — identify module
  2. Send `C,1\r` — enable 1 Hz continuous output
  3. Send `L,1\r` — enable status LED
- **Output**: conductivity in µS/cm, one reading per second
- **Power**: 3.3V or 5V — check EZO-EC module voltage requirement
- **Note**: Atlas EZO modules can be switched to I2C mode to free up UART;
  UART mode is simpler and avoids adding a 4th I2C device

### DS3231 — Real-Time Clock
- **Interface**: I2C, address 0x68
- **Accuracy**: ±2 ppm TCXO (temperature-compensated oscillator) — ~1 min/year drift
- **Backup power**: CR2032 coin cell onboard keeps time through power cycles
- **Recommended module**: Adafruit DS3231 Precision RTC (#3013) — STEMMA QT connector,
  no charging resistor risk; avoids the CR2032 damage issue present on cheap ZS-042 clones
- **MicroPython library**: `ds3231` community driver (simple; reads/writes via I2C directly)
  or adapted from the OpenCTD `RTClib` Arduino driver logic
- **Role**: authoritative time source during recording mode (no WiFi/NTP); set from NTP
  on USB connect, then Pico internal RTC is synced from DS3231 at each boot

### MicroSD Card
- **Interface**: SPI (SPI0)
- **Filesystem**: FAT32
- **MicroPython**: built-in `machine.SPI` + `sdcard` driver (available in
  MicroPython stdlib or as a small driver file)
- **File format**: CSV (see Data Format section below)

---

## State Machine

The device operates in three modes, selected automatically by USB presence:

```
                      ┌─────────────┐
          USB         │   CONFIG /  │  USB
        connected ───►│  DOWNLOAD   │◄─ connected
                      │    MODE     │
                      └──────┬──────┘
                             │ USB removed
                             ▼
                      ┌─────────────┐
                      │  RECORDING  │
                      │    MODE     │
                      └─────────────┘
```

### Config / Download Mode (USB connected)
- Serial REPL available via `mpremote` or Thonny
- WiFi enabled → NTP sync → set DS3231 RTC → sync Pico internal RTC from DS3231
- Serial command interface for:
  - Setting deployment metadata
  - Listing and downloading SD files
  - Sensor diagnostics / calibration passthrough
  - Manual data collection trigger
- RGB LED: **blue** steady (connected)

### Recording Mode (no USB, battery)
- WiFi off (power saving)
- Pico internal RTC seeded from DS3231 at boot
- Starts a new cast file on SD card
- Collects all sensors at configured interval (default: 1 Hz)
- RGB LED: **green** blink each sample; **red** blink on error
- Graceful shutdown on LiPo low-voltage (TBD — requires voltage monitor circuit)

---

## Data Format

### Cast File
One CSV file per power cycle (deployment), auto-incremented filename: `CAST000.CSV`,
`CAST001.CSV`, etc.

```csv
timestamp,pressure_mbar,depth_m,temperature_c,conductivity_uScm,f1_415nm,f2_445nm,f3_480nm,f4_515nm,f5_555nm,f6_590nm,f7_630nm,f8_680nm,clear,nir
2026-06-08T14:32:01Z,1020.5,0.21,22.34,48200,312,445,891,1203,...
```

**Timestamp**: ISO 8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`)  
**Depth**: derived from pressure using freshwater/seawater density constant (configurable)

### Deployment Metadata
A `META.TXT` file on the SD card persists deployment-level settings between
power cycles (instrument name, location, operator, calibration references, etc.).
Inherits key structure from kdupro `settings.txt`. Updated via serial command in
Config mode.

---

## MicroPython Library Dependencies

| Library | Source | Status |
|---|---|---|
| `as7341` | MicroPython port — TBD | To evaluate |
| `ms5837` | Port of Blue Robotics Python lib | To adapt |
| `tsys01` | Community MicroPython port | To evaluate |
| `ds3231` | Community MicroPython driver | To evaluate |
| `sdcard` | MicroPython stdlib / community | Available |
| `ntptime` | MicroPython stdlib | Built-in |

All third-party drivers will live in `lib/` on the Pico filesystem and in
`OpenCTDKd_multispectral/lib/` in this repo.

---

## Known Constraints and Open Questions

| Item | Status | Notes |
|---|---|---|
| AS7341 MicroPython driver | TBD | Adafruit has CircuitPython version; pure MicroPython port needed |
| MS5837 MicroPython port | TBD | Existing Python lib targets Linux/RPi; needs `machine.I2C` adaptation |
| TSYS01 MicroPython port | TBD | Simple protocol; may be easiest to implement from scratch from datasheet |
| EZO-EC UART voltage | TBD | Verify 3.3V compatibility with specific EZO-EC module version |
| LiPo voltage monitoring | TBD | May need voltage divider to Pico ADC pin for low-battery detection |
| Battery capacity | TBD | Target deployment duration not yet defined |
| Enclosure | TBD | Blue Robotics watertight enclosure assumed; size/tube diameter TBD |
| USB-detect in MicroPython | TBD | Method for reliably detecting USB connection on Pico 2W |
| RTC drift on battery | Resolved | DS3231 TCXO (±2 ppm) maintains accuracy between USB connections; Pico internal RTC seeded from DS3231 at each boot |

---

## Source References

| Resource | Location |
|---|---|
| kdupro firmware | `kdupro/firmware/src/` |
| OpenCTD m0 firmware | `OpenCTD/Software/Firmware/OpenCTD_m0/` |
| OpenCTD Bar30 firmware | `OpenCTD/Software/Firmware/OpenCTD_m0_30Bar/` |
| kdupro metadata notes | `kdupro/firmware/notes/` |
| Integration dev notes | `OpenCTDKd_multispectral/human-notes/` |
| MicroPython for Pico 2W | https://micropython.org/download/RPI_PICO2_W/ |
| Bar30 product page | https://bluerobotics.com/store/sensors-sonars-cameras/sensors/bar30-sensor-r1/ |
| Celsius sensor product page | https://bluerobotics.com/store/sensors-sonars-cameras/sensors/celsius-sensor-r1/ |
| Atlas EZO-EC datasheet | https://atlas-scientific.com/embedded-solutions/ezo-conductivity-circuit/ |
| DS3231 product page | https://www.adafruit.com/product/3013 |
| DS3231 datasheet | https://www.analog.com/media/en/technical-reference/data-sheets/DS3231.pdf |
