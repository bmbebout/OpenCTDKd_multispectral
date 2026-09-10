# OpenCTDKd Multispectral

MicroPython datalogger for underwater multispectral light and CTD sensing,
running on the Raspberry Pi Pico 2W (RP2350). See `docs/project_guide.md`
for full hardware and firmware documentation.

---

## Requirements

```bash
pip install mpremote
```

---

## Development Workflow

All commands are run from the workspace root (`kdupro_openctd_integration_work/`).
Replace `COM4` with the port shown by the device discovery command below.

### Find the Pico

```bash
mpremote connect list
```

### Verify MicroPython firmware

```bash
mpremote connect COM4 exec "import sys; print(sys.version, sys.implementation._machine)"
```

Expected output:
```
3.4.0; MicroPython v1.28.0 on 2026-04-06 Raspberry Pi Pico 2 W with RP2350
```

### Run main.py and see serial output (dev — no file copy needed)

```bash
mpremote connect COM4 run OpenCTDKd_multispectral/main.py
```

Expected output (with RTC present):
```
OpenCTDKd booting...
RTC:   2026-06-22  16:14:38
Temp:  27.0 C
System ready. (idle)
```

### Run from local source — no file copy needed (recommended for dev)

Mounts the local project directory on the Pico and runs `main.py` directly.
All serial `print()` output streams to the terminal. Edit locally and re-run —
no deploy step required.

```bash
bash OpenCTDKd_multispectral/scripts/dev_run.sh
```

Override port if needed: `bash OpenCTDKd_multispectral/scripts/dev_run.sh COM5`

### Deploy to Pico (persistent boot)

Copies all project files to the Pico filesystem. After this the Pico runs
`main.py` automatically on every power-up with no USB connection needed.

```bash
bash OpenCTDKd_multispectral/scripts/deploy.sh
```

### Watch serial output from a deployed Pico

Executes the deployed `main.py` directly from the Pico's filesystem and streams
its output to the terminal.

```bash
bash OpenCTDKd_multispectral/scripts/monitor.sh
```

---

## Project Structure

```
main.py          — entry point; boot → idle state machine
lib/
    ds3231.py    — DS3231 low-level I2C driver
    rtc.py       — RTC module (setup / read_time / set_time / read_temperature)
    neo6m.py      — NEO-6M NMEA parser
    gps.py        — GPS snapshots, quality gate, RTC sync, and metadata
    oled.py       — SSD1306 status display and rotating screens
scripts/
    dev_run.sh   — mount local source and run (no copy needed)
    deploy.sh    — copy all files to Pico for standalone boot
    monitor.sh   — connect to a deployed Pico and stream serial output
tests/
    rtc_test.py  — interactive RTC set/read utility (dev use only, not deployed)
    gps_test.py   — GPS fix and quality bring-up utility
docs/
    project_guide.md  — hardware pinout, sensor details, design decisions
dev-notes/       — dated working notes
```
