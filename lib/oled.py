"""128x32 SSD1306 OLED module on the shared I2C0 bus."""

import time
from machine import I2C, Pin

_SDA = 4
_SCL = 5
_FREQ = 100_000
_ADDR = 0x3C
_WIDTH = 128
_HEIGHT = 32

_FONT = {
    " ": (0, 0, 0, 0, 0),
    "0": (62, 81, 73, 69, 62), "1": (0, 66, 127, 64, 0),
    "2": (66, 97, 81, 73, 70), "3": (33, 65, 69, 75, 49),
    "4": (24, 20, 18, 127, 16), "5": (39, 69, 69, 69, 57),
    "6": (60, 74, 73, 73, 48), "7": (1, 113, 9, 5, 3),
    "8": (54, 73, 73, 73, 54), "9": (6, 73, 73, 41, 30),
    "A": (126, 17, 17, 17, 126), "C": (62, 65, 65, 65, 34),
    "D": (127, 65, 65, 34, 28),
    "E": (127, 73, 73, 73, 65), "L": (127, 64, 64, 64, 64),
    "N": (127, 2, 12, 16, 127), "O": (62, 65, 65, 65, 62),
    "R": (127, 9, 25, 41, 70), "S": (38, 73, 73, 73, 50),
    "T": (1, 1, 127, 1, 1),
    "I": (0, 65, 127, 65, 0), "M": (127, 2, 12, 2, 127),
    "P": (127, 9, 9, 9, 6), ".": (0, 96, 96, 0, 0),
    "Y": (3, 4, 120, 4, 3), ":": (0, 54, 54, 0, 0),
}


class SSD1306:
    def __init__(self, i2c, address=_ADDR):
        self._i2c = i2c
        self._address = address
        self._buffer = bytearray(_WIDTH * _HEIGHT // 8)
        self._command(0xAE)
        for command in (0xD5, 0x80, 0xA8, 0x1F, 0xD3, 0x00, 0x40,
                        0x8D, 0x14, 0x20, 0x00, 0xA1, 0xC8, 0xDA, 0x02,
                        0x81, 0x8F, 0xD9, 0xF1, 0xDB, 0x40, 0xA4, 0xA6,
                        0xAF):
            self._command(command)

    def clear(self):
        for index in range(len(self._buffer)):
            self._buffer[index] = 0

    def text(self, value, x=0, y=0, x_scale=1, y_scale=1):
        for character in value.upper():
            glyph = _FONT.get(character, _FONT[" "])
            if x + 5 * x_scale >= _WIDTH:
                break
            for column, bits in enumerate(glyph):
                for row in range(7):
                    if bits & (1 << row):
                        for y_repeat in range(y_scale):
                            for x_repeat in range(x_scale):
                                pixel_x = x + column * x_scale + x_repeat
                                pixel_y = y + row * y_scale + y_repeat
                                byte_index = (pixel_y // 8) * _WIDTH + pixel_x
                                self._buffer[byte_index] |= 1 << (pixel_y % 8)
            x += 6 * x_scale

    def text_right(self, value, y=0, x_scale=1, y_scale=1):
        """Draw text flush with the right edge of the display."""
        x = _WIDTH - len(value) * 6 * x_scale
        self.text(value, x, y, x_scale, y_scale)

    def show(self):
        self._command(0xAE)
        try:
            self._command(0x21, 0, _WIDTH - 1)
            self._command(0x22, 0, (_HEIGHT // 8) - 1)
            for offset in range(0, len(self._buffer), 32):
                self._i2c.writeto(self._address, b"\x40" +
                                  self._buffer[offset:offset + 32])
        finally:
            self._command(0xAF)

    def _command(self, *commands):
        self._i2c.writeto(self._address, b"\x00" + bytes(commands))


def setup():
    """Initialise and return the OLED. Raises OSError if it is not found."""
    global _last_switch_ms
    i2c = I2C(0, sda=Pin(_SDA), scl=Pin(_SCL), freq=_FREQ)
    if _ADDR not in i2c.scan():
        raise OSError("SSD1306 OLED not found on I2C0 (0x3C) — check wiring")
    display = SSD1306(i2c)
    display.clear()
    display.text("NOT RDY", 0, 0, 1, 2)
    display.text("LINES:0", 0, 16, 1, 2)
    display.show()
    _last_switch_ms = time.ticks_ms()
    print("OLED:  SSD1306 128x32 ready")
    return display


_screen = 0
_last_switch_ms = 0
_last_render_key = None


def update(display, ready, line_count, clear_value=None, temperature_c=None):
    """Rotate between readiness/lines and Clear/temperature screens."""
    global _screen, _last_switch_ms, _last_render_key
    if display is None:
        return
    try:
        now_ms = time.ticks_ms()
        if time.ticks_diff(now_ms, _last_switch_ms) >= 2000:
            _screen = (_screen + 1) % 2
            _last_switch_ms = now_ms
        render_key = (_screen, ready, line_count, clear_value, temperature_c)
        if render_key == _last_render_key:
            return
        display.clear()
        if _screen == 0:
            display.text("READY" if ready else "NOT RDY", 0, 0, 1, 2)
            display.text("LINES:%d" % line_count, 0, 16, 1, 2)
        else:
            display.text("CLEAR:", 0, 0, 1, 2)
            clear_text = "--" if clear_value is None else str(int(clear_value))
            display.text_right(clear_text, 0, 1, 2)
            display.text("T:", 0, 16, 1, 2)
            temperature_text = "--C" if temperature_c is None else "%.1fC" % temperature_c
            display.text_right(temperature_text, 16, 1, 2)
        display.show()
        _last_render_key = render_key
    except OSError as e:
        print("OLED update error:", e)