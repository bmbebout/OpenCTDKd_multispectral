"""NEO-6M-compatible GPS receiver driver for MicroPython.

Parses the NMEA RMC and GGA sentences emitted by the GY-GPS6MU2 breakout.
"""

import time


class NEO6M:
    def __init__(self, uart):
        self._uart = uart
        self._fix = False
        self._latitude = None
        self._longitude = None
        self._altitude_m = None
        self._satellites = 0
        self._utc = None
        self._seen_sentence = False
        self._rmc_valid = False
        self._gga_quality = 0
        self._hdop = None

    def update(self):
        """Read and parse available NMEA sentences without blocking."""
        updated = False
        for _ in range(12):
            line = self._uart.readline()
            if not line:
                break
            try:
                sentence = line.decode().strip()
            except UnicodeError:
                continue
            if self._parse(sentence):
                self._seen_sentence = True
                updated = True
        return updated

    def wait_for_fix(self, timeout_ms=10000):
        """Poll until a valid position is received or the timeout expires."""
        deadline = time.ticks_add(time.ticks_ms(), timeout_ms)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            self.update()
            if self._fix:
                return True
            time.sleep_ms(100)
        return self._fix

    def snapshot(self, poll=True):
        """Return the latest position and UTC data, optionally polling first."""
        if poll:
            self.update()
        return {
            "fix": self._fix,
            "latitude": self._latitude,
            "longitude": self._longitude,
            "altitude_m": self._altitude_m,
            "satellites": self._satellites,
            "quality_code": self._gga_quality,
            "hdop": self._hdop,
            "utc": self._utc,
        }

    def _parse(self, sentence):
        if not sentence.startswith("$"):
            return False
        fields = sentence.split(",")
        if len(fields) < 2:
            return False
        kind = fields[0][3:]
        if kind == "RMC":
            return self._parse_rmc(fields)
        if kind == "GGA":
            return self._parse_gga(fields)
        return False

    def _parse_rmc(self, fields):
        if len(fields) < 10:
            return False
        self._utc = _parse_datetime(fields[1], fields[9])
        if fields[2] != "A":
            self._rmc_valid = False
            self._update_fix()
            return True
        latitude = _parse_coordinate(fields[3], fields[4], 2)
        longitude = _parse_coordinate(fields[5], fields[6], 3)
        if latitude is None or longitude is None:
            return False
        self._latitude = latitude
        self._longitude = longitude
        self._rmc_valid = True
        self._update_fix()
        return True

    def _parse_gga(self, fields):
        if len(fields) < 10:
            return False
        try:
            self._gga_quality = int(fields[6] or "0")
        except ValueError:
            self._gga_quality = 0
        if self._gga_quality > 0:
            latitude = _parse_coordinate(fields[2], fields[3], 2)
            longitude = _parse_coordinate(fields[4], fields[5], 3)
            if latitude is not None and longitude is not None:
                self._latitude = latitude
                self._longitude = longitude
        self._update_fix()
        if fields[7]:
            try:
                self._satellites = int(fields[7])
            except ValueError:
                self._satellites = 0
        if fields[9]:
            try:
                self._altitude_m = float(fields[9])
            except ValueError:
                self._altitude_m = None
        if fields[8]:
            try:
                self._hdop = float(fields[8])
            except ValueError:
                self._hdop = None
        return True

    def _update_fix(self):
        self._fix = self._rmc_valid and self._gga_quality > 0


def _parse_coordinate(value, hemisphere, degree_digits):
    if not value or not hemisphere:
        return None
    try:
        degrees = float(value[:degree_digits])
        minutes = float(value[degree_digits:])
        coordinate = degrees + minutes / 60.0
        return -coordinate if hemisphere in ("S", "W") else coordinate
    except (ValueError, IndexError):
        return None


def _parse_datetime(time_text, date_text):
    if len(time_text) < 6 or len(date_text) != 6:
        return None
    try:
        hour = int(time_text[0:2])
        minute = int(time_text[2:4])
        second = int(float(time_text[4:]))
        day = int(date_text[0:2])
        month = int(date_text[2:4])
        year = 2000 + int(date_text[4:6])
        return (year, month, day, hour, minute, second)
    except ValueError:
        return None