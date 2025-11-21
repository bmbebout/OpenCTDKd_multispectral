# OpenCTDKd Multispectral - MicroPython Project

A MicroPython-based project for the OpenCTD with multispectral sensing capabilities.

## Setup

### Install mpremote

```bash
pip install mpremote
```

## Usage

### Upload and Run Code

Upload `main.py` to the device and run it:
```bash
mpremote connect COM3 cp main.py :main.py run main.py
```

Replace `COM3` with your device's serial port (use `mpremote connect list` to find it).

### Quick Commands

**List available devices:**
```bash
mpremote connect list
```

**Copy file to device:**
```bash
mpremote cp main.py :main.py
```

**Run code directly without saving:**
```bash
mpremote run main.py
```

**Access REPL:**
```bash
mpremote
```

**Soft reset the device:**
```bash
mpremote reset
```

**View filesystem:**
```bash
mpremote ls
```

**Remove a file:**
```bash
mpremote rm :main.py
```

## Hello World Example

The included `main.py` blinks the onboard LED and prints messages to demonstrate basic MicroPython functionality.

## Development Workflow

1. Edit your Python files locally
2. Use `mpremote cp` to upload to device
3. Use `mpremote run` to test quickly
4. Use `mpremote` (REPL) for interactive debugging
5. When ready, copy to `:main.py` to run on boot

## Troubleshooting

- If the device isn't detected, check that it's plugged in and drivers are installed
- On Windows, the port is usually `COM3`, `COM4`, etc.
- On Linux/Mac, it's usually `/dev/ttyUSB0` or `/dev/ttyACM0`
- Use `mpremote connect list` to see all connected MicroPython devices
