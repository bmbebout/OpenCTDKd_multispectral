"""Atlas Scientific EZO-EC conductivity sensor driver for MicroPython (I2C).

Protocol (per Atlas Scientific EZO-EC datasheet):
    Write: null-terminated ASCII command string to device address
    Wait:  ≥300 ms (most commands), ≥600 ms for R, ≥900 ms for CAL
    Read:  up to 31 bytes; byte 0 = response code, bytes 1+ = null-terminated ASCII
           Response codes: 1=success, 2=syntax error, 254=still processing, 255=no data

Default I2C address: 0x62 (98 decimal).
    To change address: send "I2C,[new_addr]" command.
    To switch from UART to I2C mode: short PGND pin to TX pin on power-up.

R command output: "EC,TDS,SAL,SG" (comma-separated)
    EC  = conductivity in µS/cm
    TDS = total dissolved solids in ppm
    SAL = salinity in PSU (practical salinity units)
    SG  = specific gravity relative to pure water
"""

import time

_ADDR         = const(0x64)  # Atlas Scientific default: 100 decimal
_RESP_SUCCESS = const(1)
_READ_LEN     = const(31)

# Command processing delays (ms) — from EZO-EC datasheet
_DELAY_STD_MS = const(300)
_DELAY_READ_MS = const(600)
_DELAY_CAL_MS  = const(900)


class EZO_EC:
    def __init__(self, i2c, addr=_ADDR):
        self._i2c  = i2c
        self._addr = addr
        # Updated by read()
        self.ec               = 0.0  # µS/cm
        self.tds              = 0.0  # ppm
        self.salinity         = 0.0  # PSU
        self.specific_gravity = 0.0
        self._verify()

    def _cmd(self, command, delay_ms):
        """Send ASCII command and return decoded response string, or None on failure."""
        self._i2c.writeto(self._addr, command.encode() + b'\x00')
        time.sleep_ms(delay_ms)
        raw = self._i2c.readfrom(self._addr, _READ_LEN)
        if raw[0] != _RESP_SUCCESS:
            return None
        # Find null terminator after status byte; bytes.index(x, start) unsupported in MicroPython
        end = len(raw)
        for i in range(1, len(raw)):
            if raw[i] == 0:
                end = i
                break
        return raw[1:end].decode()

    def _verify(self):
        """Confirm device is responding (sends I command for device info)."""
        resp = self._cmd("I", _DELAY_STD_MS)
        if resp is None:
            raise OSError("EZO-EC not responding at 0x%02x — verify I2C mode (LED must be solid blue)" % self._addr)

    def read(self, temperature_c=None):
        """Take a reading; update ec, tds, salinity, specific_gravity attributes.
        temperature_c: float °C from TSYS01 — sends T command before reading for compensation."""
        if temperature_c is not None:
            self._cmd("T,%.2f" % temperature_c, _DELAY_STD_MS)
        resp = self._cmd("R", _DELAY_READ_MS)
        if resp is None:
            raise OSError("EZO-EC: no reading returned — probe may need calibration")
        parts = resp.split(",")
        self.ec               = float(parts[0])
        self.tds              = float(parts[1]) if len(parts) > 1 else 0.0
        self.salinity         = float(parts[2]) if len(parts) > 2 else 0.0
        self.specific_gravity = float(parts[3]) if len(parts) > 3 else 0.0
