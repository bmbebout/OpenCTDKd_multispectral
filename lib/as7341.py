"""AS7341 10-channel spectral sensor driver for MicroPython (I2C).

The AS7341 contains 10 photodiode channels (F1-F8, Clear, NIR) mapped to 6
hardware ADC channels via a configurable SMUX.  Reading all 10 channels
requires two measurement passes with different SMUX configurations:

  Pass 1 — SMUX_F1_F4:  ADC0=F1(415nm), ADC1=F2(445nm), ADC2=F3(480nm),
                         ADC3=F4(515nm), ADC4=Clear, ADC5=NIR
  Pass 2 — SMUX_F5_F8:  ADC0=F5(555nm), ADC1=F6(590nm), ADC2=F7(630nm),
                         ADC3=F8(680nm), ADC4=Clear, ADC5=NIR

SMUX byte values (20 bytes, written to I2C registers 0x00-0x13) were derived
from the Adafruit CircuitPython AS7341 library (MIT licence, Bryan Siepert).
Each byte encodes two ADC assignments: bits[3:0] = out1, bits[7:4] = out2.
"""

import time

_ADDR    = const(0x39)

# Key register addresses
_ENABLE  = const(0x80)   # PON=bit0, SP_EN=bit1, SMUXEN=bit4
_ATIME   = const(0x81)   # integration step count (0-255)
_STATUS2 = const(0xA3)   # bit6 = AVALID (data ready)
_CFG0    = const(0xA9)   # bit4 = BANK (low-bank access for LED regs)
_CFG1    = const(0xAA)   # bits[4:0] = AGAIN gain index
_CFG6    = const(0xAF)   # bits[4:3] = SMUX_CMD (2 = write SMUX RAM)
_ASTEP_L = const(0xCA)   # integration step size LSB (little-endian 16-bit)
_ASTEP_H = const(0xCB)   # integration step size MSB
_ASTATUS = const(0x94)   # reading this register latches all 12 channel bytes
_CH0_L   = const(0x95)   # first channel data register (6 × 2 bytes follow)
_WHOAMI  = const(0x92)   # chip ID register; bits[7:2] should equal 0x09

# SMUX configuration byte arrays (one byte per SMUX register 0x00-0x13).
# Derived from Adafruit CircuitPython AS7341 library _f1f4_clear_nir() and
# _f5f8_clear_nir() by resolving each _set_smux() call to its byte value.
_SMUX_F1_F4 = bytes([
    0x30, 0x01, 0x00, 0x00, 0x00, 0x42, 0x00, 0x00,
    0x50, 0x00, 0x00, 0x00, 0x20, 0x04, 0x00, 0x30,
    0x01, 0x50, 0x00, 0x06,
])
_SMUX_F5_F8 = bytes([
    0x00, 0x00, 0x00, 0x40, 0x02, 0x00, 0x10, 0x03,
    0x50, 0x10, 0x03, 0x00, 0x00, 0x00, 0x24, 0x00,
    0x00, 0x50, 0x00, 0x06,
])

# AGAIN gain index → actual multiplier
GAIN_MAP = {0: 0.5, 1: 1, 2: 2, 3: 4, 4: 8, 5: 16,
            6: 32, 7: 64, 8: 128, 9: 256, 10: 512}


class AS7341:
    """Minimal AS7341 driver: read all 10 spectral channels."""

    def __init__(self, i2c, addr=_ADDR, atime=100, astep=500, gain=8):
        """Initialise and verify the sensor.

        i2c:   MicroPython I2C instance
        addr:  I2C address (default 0x39)
        atime: integration step count 0-255   (default 100)
        astep: integration step size 0-65534  (default 500)
        gain:  AGAIN index 0-10               (default 8 = 128×)

        Integration time per pass = (atime+1) × (astep+1) × 2.78 µs
        With defaults: 101 × 501 × 2.78 µs ≈ 141 ms per pass.
        """
        self._i2c  = i2c
        self._addr = addr

        whoami = self._read8(_WHOAMI)
        if (whoami >> 2) & 0x3F != 0x09:
            raise OSError(f"AS7341 not found at 0x{addr:02X} "
                          f"(WHOAMI=0x{whoami:02X}, expected bits[7:2]=0x09)")

        # Power on and configure timing / gain
        self._write8(_ENABLE, 0x01)          # PON = 1
        time.sleep_ms(10)
        self._write8(_ATIME, atime)
        self._write8(_ASTEP_L, astep & 0xFF) # ASTEP is 16-bit little-endian
        self._write8(_ASTEP_H, (astep >> 8) & 0xFF)
        self._write8(_CFG1, gain & 0x1F)     # AGAIN in bits[4:0]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def read_all_channels(self):
        """Read all 10 spectral channels in two SMUX passes.

        Returns a dict keyed by channel name:
            F1_415nm, F2_445nm, F3_480nm, F4_515nm,
            F5_555nm, F6_590nm, F7_630nm, F8_680nm,
            clear, nir
        Values are raw 16-bit ADC counts (0-65535).
        """
        f1_f4 = self._measure(_SMUX_F1_F4)  # CH0-CH5 for first pass
        f5_f8 = self._measure(_SMUX_F5_F8)  # CH0-CH5 for second pass
        return {
            "F1_415nm": f1_f4[0],
            "F2_445nm": f1_f4[1],
            "F3_480nm": f1_f4[2],
            "F4_515nm": f1_f4[3],
            "F5_555nm": f5_f8[0],
            "F6_590nm": f5_f8[1],
            "F7_630nm": f5_f8[2],
            "F8_680nm": f5_f8[3],
            "clear":    f5_f8[4],
            "nir":      f5_f8[5],
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _measure(self, smux_bytes):
        """Run one full SMUX measurement pass and return 6 ADC counts.

        Sequence (per AS7341 datasheet Section 10.2):
          1. Disable spectral measurement (clear SP_EN)
          2. Write SMUX RAM (20 bytes to registers 0x00-0x13)
          3. Execute SMUX load (set SMUXEN; hardware auto-clears when done)
          4. Re-enable spectral measurement (set SP_EN)
          5. Wait for AVALID (STATUS2 bit 6)
          6. Read ASTATUS to latch, then read 12 data bytes
        """
        # Step 1: disable spectral engine while reconfiguring
        self._write8(_ENABLE, self._read8(_ENABLE) & ~0x02)

        # Step 2 & 3: load SMUX configuration
        self._write8(_CFG6, 0x10)                        # SMUX_CMD = 0b10
        self._i2c.writeto_mem(self._addr, 0x00, smux_bytes)  # write 20 bytes
        self._write8(_ENABLE, self._read8(_ENABLE) | 0x10)   # set SMUXEN
        deadline = time.ticks_ms() + 1000
        while self._read8(_ENABLE) & 0x10:               # wait for auto-clear
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                raise OSError("AS7341: SMUX load timeout")

        # Step 4: enable spectral measurement
        self._write8(_ENABLE, self._read8(_ENABLE) | 0x02)

        # Step 5: wait for data ready
        deadline = time.ticks_ms() + 5000
        while not (self._read8(_STATUS2) & 0x40):        # AVALID bit
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                raise OSError("AS7341: measurement timeout")
            time.sleep_ms(1)

        # Step 6: read ASTATUS (latches data) then read 12 data bytes
        self._read8(_ASTATUS)
        raw = self._i2c.readfrom_mem(self._addr, _CH0_L, 12)
        return [raw[i] | (raw[i + 1] << 8) for i in range(0, 12, 2)]

    def _read8(self, reg):
        """Read one byte from reg."""
        return self._i2c.readfrom_mem(self._addr, reg, 1)[0]

    def _write8(self, reg, val):
        """Write one byte to reg."""
        self._i2c.writeto_mem(self._addr, reg, bytes([val & 0xFF]))
