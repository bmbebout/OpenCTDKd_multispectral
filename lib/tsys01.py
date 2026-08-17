"""TSYS01 precision temperature sensor driver for MicroPython (I2C).

Protocol (two phases per reading):
  1. Init  — reset, read 5 PROM calibration words (k0..k4)
  2. Read  — trigger ADC conversion, read 3-byte result, apply polynomial

Calibration formula and PROM layout ported from the Blue Robotics
tsys01-python library (MIT licence, https://github.com/bluerobotics/tsys01-python).
"""

import time

_ADDR        = const(0x77)
_CMD_RESET   = const(0x1E)
_CMD_CONVERT = const(0x48)  # single conversion command (~9 ms max)
_CMD_READ    = const(0x00)  # read 3-byte ADC result

# PROM addresses, read high-to-low: k[0]=k0 (0xAA) .. k[4]=k4 (0xA2)
_PROM_ADDRS  = (0xAA, 0xA8, 0xA6, 0xA4, 0xA2)


class TSYS01:
    def __init__(self, i2c, addr=_ADDR):
        self._i2c  = i2c
        self._addr = addr
        self._k    = []
        self.temperature = 0.0  # °C, updated by read()
        self._init()

    def _init(self):
        self._i2c.writeto(self._addr, bytes([_CMD_RESET]))
        time.sleep_ms(15)

        # Read 5 factory calibration words; order matches formula indexing
        self._k = []
        for prom in _PROM_ADDRS:
            self._i2c.writeto(self._addr, bytes([prom]))
            d = self._i2c.readfrom(self._addr, 2)
            self._k.append((d[0] << 8) | d[1])

    def read(self):
        """Trigger one conversion and update the temperature attribute."""
        self._i2c.writeto(self._addr, bytes([_CMD_CONVERT]))
        time.sleep_ms(12)  # datasheet max 9.04 ms; extra margin
        self._i2c.writeto(self._addr, bytes([_CMD_READ]))
        d   = self._i2c.readfrom(self._addr, 3)
        adc = (d[0] << 16) | (d[1] << 8) | d[2]
        self._calculate(adc)

    def _calculate(self, adc):
        """Polynomial conversion per TSYS01 datasheet Table 2."""
        k   = self._k
        a   = adc / 256.0   # scale to 16-bit equivalent
        self.temperature = (
            -2.0   * k[4] * 1e-21 * a**4
            + 4.0  * k[3] * 1e-16 * a**3
            - 2.0  * k[2] * 1e-11 * a**2
            + 1.0  * k[1] * 1e-6  * a
            - 1.5  * k[0] * 1e-2
        )
