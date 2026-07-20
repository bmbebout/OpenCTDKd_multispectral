# MicroPython Install on Raspberry Pi Pico 2W

**Date:** 2026-06-08  
**Firmware:** MicroPython v1.28.0 (2026-04-06)  
**Board:** Raspberry Pi Pico 2W (RP2350)

---

## Prerequisites

- `mpremote` installed (`pip install mpremote`)
- `pyserial` installed (`pip install pyserial`)
- Pico 2W connected via data-capable USB cable

---

## Steps

### 1. Enter BOOTSEL mode

Hold the **BOOTSEL** button on the Pico while plugging in the USB cable. The board mounts as a removable drive (label `RP2350`, appeared as `D:\` in this case).

### 2. Download and flash MicroPython firmware

Download the latest stable `.uf2` for the Pico 2W from:  
https://micropython.org/download/RPI_PICO2_W/

Write it directly to the Pico drive (replace `D:` with actual drive letter):

```powershell
Invoke-WebRequest -Uri 'https://micropython.org/resources/firmware/RPI_PICO2_W-20260406-v1.28.0.uf2' -OutFile 'D:\RPI_PICO2_W-20260406-v1.28.0.uf2'
```

The Pico reboots automatically once the file is written.

### 3. Verify COM port

```bash
python -c "import serial.tools.list_ports; [print(p.device, p.description) for p in serial.tools.list_ports.comports()]"
```

Expected output: `COM4 - USB Serial Device (COM4)` (port number may vary).

### 4. Run a script with mpremote

```bash
mpremote connect COM4 run OpenCTDKd_multispectral/main.py
```

Confirmed working: `main.py` (LED blink) ran successfully, printing output to terminal.

---

## Notes

- `mpremote` without a port specified will auto-detect; explicit `connect COMx` is more reliable on Windows.
- The Pico 2W USB VID is `0x2E8A` — useful for confirming device detection via `Get-WMIObject Win32_USBHub`.
