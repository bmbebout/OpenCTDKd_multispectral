# EZO-RTD Integration Attempt

Date: 2026-10-05

## Objective

Connect the Atlas Scientific Industrial conductivity probe and use its RTD
through an Atlas Scientific EZO-RTD circuit for temperature-compensated EZO-EC
conductivity measurements.

## Firmware Changes

- Added `lib/ezo_rtd.py`, an I2C driver for the EZO-RTD.
- Updated `lib/temperature.py` to use the EZO-RTD at I2C address `0x66`.
- Existing EZO-EC conductivity compensation now receives the EZO-RTD reading.
- Added the EZO-RTD to the deployment script and temperature bring-up test.
- Firmware compiled successfully and was deployed to the Pico on COM4.

## Hardware Attempt

The EZO-RTD carrier exposed `TX` and `RX` terminals rather than terminals
labelled SDA and SCL. These terminals are expected to become SDA and SCL only
after the circuit is switched from UART to I2C mode.

The Pico I2C scan returned:

```text
0x39, 0x3c, 0x64, 0x68, 0x76, 0x77
```

EZO-EC responded at `0x64`, but the EZO-RTD did not respond at `0x66`.
The temperature bring-up test therefore failed before taking readings:

```text
FAIL: EZO-RTD not found on I2C0 (0x66)
```

## Conclusion

The software integration is prepared, but the EZO-RTD remains in UART mode or
is otherwise not visible on the I2C bus. The hardware mode-switch attempt was
unsuccessful. The next step is to connect the EZO-RTD to a 3.3 V-compatible
USB-to-serial adapter and send `I2C,102` at 9600 baud, then power-cycle and
confirm a solid-blue LED and I2C address `0x66` before reconnecting it to the
Pico.

Update 2026-10-14: resolved. See `261014_ezo_rtd_ec_compensation.md`.
