"""Atlas Scientific EZO-RTD temperature circuit driver for MicroPython (I2C).

Protocol (per Atlas Scientific EZO-RTD datasheet):
    Write: null-terminated ASCII command string to device address
    Wait:  >=300 ms (most commands), >=600 ms for R
    Read:  up to 31 bytes; byte 0 = response code, bytes 1+ = null-terminated ASCII
           Response codes: 1=success, 2=syntax error, 254=still processing, 255=no data

Default I2C address: 0x66 (102 decimal).
    To switch from UART to I2C mode: send "I2C,102" over UART (9600 baud), then power-cycle.
    In I2C mode the carrier's TX terminal is SDA and RX terminal is SCL.

R command output: temperature as a decimal string, e.g. "23.605" (scale set by S command).
"""

import time

_ADDR         = const(0x66)  # Atlas Scientific default: 102 decimal
_RESP_SUCCESS = const(1)
_READ_LEN     = const(31)

# Command processing delays (ms) - from EZO-RTD datasheet
_DELAY_STD_MS  = const(300)
_DELAY_READ_MS = const(600)


class EZO_RTD:
    def __init__(self, i2c, addr=_ADDR):
        self._i2c  = i2c
        self._addr = addr
        self._started = None  # ticks_ms of an in-flight R conversion, else None
        self.temperature = 0.0  # degC, updated by read()
        self._verify()

    def _cmd(self, command, delay_ms):
        """Send ASCII command and return decoded response string, or None on failure."""
        self._i2c.writeto(self._addr, command.encode() + b'\x00')
        time.sleep_ms(delay_ms)
        return self._response()

    def _response(self):
        """Read the pending response; return decoded string, or None if not successful."""
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
        """Confirm an RTD circuit is responding and force the Celsius scale.
        Retries because a conversion left over from before a reset either blocks
        the command (code 254) or answers with its stale reading instead of the
        device info."""
        for _ in range(3):
            resp = self._cmd("i", _DELAY_STD_MS)
            if resp is not None and "RTD" in resp:
                break
        else:
            raise OSError("EZO-RTD not responding at 0x%02x - verify I2C mode (LED must be blue)" % self._addr)
        # The circuit reports its scale in upper case ("?S,C"); only write when it differs
        scale = self._cmd("S,?", _DELAY_STD_MS)
        if scale is None or scale.lower() != "?s,c":
            self._cmd("S,c", _DELAY_STD_MS)

    def start(self):
        """Begin a conversion without waiting, so it overlaps other bus work; read() collects it."""
        self._i2c.writeto(self._addr, b"R\x00")
        self._started = time.ticks_ms()

    def read(self):
        """Collect a reading (starting one if none is in flight) and update temperature (degC)."""
        if self._started is None:
            self.start()
        remaining = _DELAY_READ_MS - time.ticks_diff(time.ticks_ms(), self._started)
        if remaining > 0:
            time.sleep_ms(remaining)
        self._started = None
        resp = self._response()
        if resp is None:
            raise OSError("EZO-RTD: no reading returned")
        self.temperature = float(resp)
