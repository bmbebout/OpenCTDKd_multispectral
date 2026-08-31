# EZO-EC Conductivity Sensor — I2C vs UART

**Date:** 2026-08-17

---

## Decision: I2C

EZO-EC default I2C address `0x62` — no conflict with existing bus devices (`0x39`, `0x68`, `0x76`, `0x77`).

---

## Command set is identical on both interfaces

Every calibration and operational command (`R`, `CAL,dry`, `CAL,low,x`, `CAL,high,x`, `T,x`, `STATUS`, `SLEEP`, etc.) works over both I2C and UART. The protocol framing differs, not the capabilities.

| | I2C | UART |
|---|---|---|
| Write | null-terminated string | string + `\r` |
| Read | up to 31 bytes; byte 0 = status code | read until `\r` |
| Short timeout | 300 ms | ~300 ms |
| R / CAL timeout | 1500 ms | ~1300 ms |
| Continuous mode | not supported | `C,1` auto-emit |

## What UART adds

The only exclusive UART feature is `C,1` continuous mode, where the EZO emits readings autonomously without polling. At 1 reading/s this is irrelevant — a single `R` command per log cycle is equivalent.

The Atlas FTDI mode is a bench-calibration convenience (USB-to-serial terminal). The same calibration commands can be sent over I2C from the MicroPython REPL.

## Why the datasheet calls UART simpler

The Atlas Raspberry Pi library (`AtlasI2C.py`) uses Linux `/dev/i2c-*` file handles and `fcntl.ioctl` calls to address the slave. That's Linux-specific boilerplate. With `machine.I2C` in MicroPython the I2C path is actually shorter than `pyserial` UART.

## MicroPython I2C protocol

```
i2c.writeto(0x62, b"R\x00")
time.sleep_ms(1500)
data = i2c.readfrom(0x62, 31)
# data[0] == 1 → success; data[1:] = null-terminated reading string
```
