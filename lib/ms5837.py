"""MS5837-30BA pressure/temperature sensor driver for MicroPython (I2C).

Protocol (3 phases per reading):
  1. Init  — reset, read 7 PROM calibration words, verify CRC4
  2. Read  — trigger D1 (pressure) and D2 (temperature) ADC conversions
  3. Calc  — apply second-order compensation formula (MS5837-30BA datasheet)

Compensation formula and CRC4 ported from the Blue Robotics ms5837-python
library (MIT licence, https://github.com/bluerobotics/ms5837-python).
"""

import time

_ADDR        = const(0x76)
_CMD_RESET   = const(0x1E)
_CMD_ADC     = const(0x00)  # read ADC result (3 bytes)
_CMD_CONV_D1 = const(0x40)  # pressure conversion; OR with 2*osr
_CMD_CONV_D2 = const(0x50)  # temperature conversion; OR with 2*osr
_CMD_PROM    = const(0xA0)  # PROM read base; add 2*i for word i (i = 0..6)

# Oversampling rate constants (used as index and as command offset)
OSR_256  = 0
OSR_512  = 1
OSR_1024 = 2
OSR_2048 = 3
OSR_4096 = 4
OSR_8192 = 5  # best accuracy, ~21 ms conversion time

# Maximum ADC conversion time per OSR level (ms)
_CONV_MS = (1, 2, 3, 6, 11, 21)

DENSITY_FRESHWATER = 997   # kg/m³
DENSITY_SALTWATER  = 1029  # kg/m³


class MS5837:
    def __init__(self, i2c, addr=_ADDR):
        self._i2c  = i2c
        self._addr = addr
        self._C    = []
        self.pressure    = 0.0  # mbar, updated by read()
        self.temperature = 0.0  # °C,   updated by read()
        self._init()

    def _init(self):
        self._i2c.writeto(self._addr, bytes([_CMD_RESET]))
        time.sleep_ms(10)

        # Read 7 factory calibration words from PROM (C0..C6)
        self._C = []
        for i in range(7):
            self._i2c.writeto(self._addr, bytes([_CMD_PROM + 2 * i]))
            d = self._i2c.readfrom(self._addr, 2)
            self._C.append((d[0] << 8) | d[1])

        crc = (self._C[0] & 0xF000) >> 12
        if crc != self._crc4(list(self._C)):
            raise OSError("MS5837: PROM CRC mismatch — check wiring or power")

    def read(self, osr=OSR_8192):
        """Trigger ADC conversions and update pressure/temperature attributes.
        osr: OSR_256..OSR_8192 — higher OSR = more accurate, slower."""
        self._i2c.writeto(self._addr, bytes([_CMD_CONV_D1 + 2 * osr]))
        time.sleep_ms(_CONV_MS[osr])
        self._i2c.writeto(self._addr, bytes([_CMD_ADC]))
        d  = self._i2c.readfrom(self._addr, 3)
        D1 = (d[0] << 16) | (d[1] << 8) | d[2]

        self._i2c.writeto(self._addr, bytes([_CMD_CONV_D2 + 2 * osr]))
        time.sleep_ms(_CONV_MS[osr])
        self._i2c.writeto(self._addr, bytes([_CMD_ADC]))
        d  = self._i2c.readfrom(self._addr, 3)
        D2 = (d[0] << 16) | (d[1] << 8) | d[2]

        self._calculate(D1, D2)

    def depth(self, density=DENSITY_FRESHWATER):
        """Depth in metres from current pressure reading.
        Assumes 101300 Pa surface atmospheric pressure."""
        return (self.pressure * 100 - 101300) / (density * 9.80665)

    def _calculate(self, D1, D2):
        """MS5837-30BA second-order temperature-compensated conversion."""
        C = self._C

        dT   = D2 - C[5] * 256
        TEMP = 2000 + dT * C[6] // 8388608

        SENS = C[1] * 32768 + (C[3] * dT) // 256
        OFF  = C[2] * 65536 + (C[4] * dT) // 128

        # Second-order compensation (per datasheet Table 9)
        Ti = OFFi = SENSi = 0
        if TEMP < 2000:                              # below 20 °C
            Ti    = 3 * dT * dT // 8589934592
            OFFi  = 3 * (TEMP - 2000) ** 2 // 2
            SENSi = 5 * (TEMP - 2000) ** 2 // 8
            if TEMP < -1500:                         # below -15 °C
                OFFi  += 7 * (TEMP + 1500) ** 2
                SENSi += 4 * (TEMP + 1500) ** 2
        else:                                        # at or above 20 °C
            Ti    = 2 * dT * dT // 137438953472
            OFFi  = (TEMP - 2000) ** 2 // 16

        OFF2  = OFF  - OFFi
        SENS2 = SENS - SENSi

        self.temperature = (TEMP - Ti) / 100.0
        self.pressure    = (D1 * SENS2 // 2097152 - OFF2) / 8192 / 10.0

    @staticmethod
    def _crc4(prom):
        """CRC4 verification per MS5837 datasheet Table 15."""
        prom[0] &= 0x0FFF
        prom.append(0)
        n_rem = 0
        for i in range(16):
            n_rem ^= (prom[i >> 1] >> 8) if (i % 2 == 0) else (prom[i >> 1] & 0xFF)
            for _ in range(8):
                n_rem = (n_rem << 1) ^ 0x3000 if (n_rem & 0x8000) else (n_rem << 1)
        return (n_rem >> 12) & 0x000F
