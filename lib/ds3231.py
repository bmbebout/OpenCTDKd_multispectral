"""DS3231 precision RTC driver for MicroPython over I2C."""

_DS3231_ADDR = 0x68
_REG_TIME = 0x00   # start of 7-byte time block (sec, min, hr, dow, date, mon, yr)
_REG_TEMP = 0x11   # 2-byte temperature register


def _bcd_to_int(bcd):
    return (bcd >> 4) * 10 + (bcd & 0x0F)


def _int_to_bcd(n):
    return ((n // 10) << 4) | (n % 10)


class DS3231:
    """Minimal DS3231 driver: read/set datetime, read temperature."""

    def __init__(self, i2c, addr=_DS3231_ADDR):
        self._i2c = i2c
        self._addr = addr

    def get_datetime(self):
        """Return (year, month, day, hour, minute, second, weekday).
        weekday is DS3231-defined 1–7; not relied on for display."""
        d = self._i2c.readfrom_mem(self._addr, _REG_TIME, 7)
        second  = _bcd_to_int(d[0] & 0x7F)        # mask oscillator-stop flag
        minute  = _bcd_to_int(d[1])
        hour    = _bcd_to_int(d[2] & 0x3F)        # mask 12/24-hour mode bit
        weekday = d[3] & 0x07
        day     = _bcd_to_int(d[4])
        month   = _bcd_to_int(d[5] & 0x1F)        # mask century bit
        year    = _bcd_to_int(d[6]) + 2000
        return (year, month, day, hour, minute, second, weekday)

    def set_datetime(self, year, month, day, hour, minute, second, weekday=1):
        """Write datetime to DS3231. year is full (e.g. 2026).
        weekday 1–7 is user-defined; defaults to 1 if unused."""
        data = bytes([
            _int_to_bcd(second),
            _int_to_bcd(minute),
            _int_to_bcd(hour),        # written in 24-hour format
            weekday & 0x07,
            _int_to_bcd(day),
            _int_to_bcd(month),
            _int_to_bcd(year - 2000),
        ])
        self._i2c.writeto_mem(self._addr, _REG_TIME, data)

    def temperature(self):
        """Return DS3231 internal temperature in °C (0.25 °C resolution).
        Valid range: –40 to +85 °C."""
        raw = self._i2c.readfrom_mem(self._addr, _REG_TEMP, 2)
        # 10-bit signed value: raw[0] = integer part, raw[1] bits 7:6 = fraction
        temp_raw = (raw[0] << 2) | (raw[1] >> 6)
        if temp_raw > 511:          # two's complement: sign bit set
            temp_raw -= 1024
        return temp_raw * 0.25
