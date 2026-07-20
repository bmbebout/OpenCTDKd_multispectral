"""RTC test utility — DS3231 on I2C0 (SDA=GPIO4, SCL=GPIO5).

Wiring:
    DS3231 VIN  → Pico 3.3V  (pin 36)
    DS3231 GND  → Pico GND   (pin 38)
    DS3231 SDA  → GPIO4      (pin 6)
    DS3231 SCL  → GPIO5      (pin 7)

Deploy and run (development mode using local mount):
    mpremote connect COM4 mount OpenCTDKd_multispectral run rtc_test.py

Or copy files to Pico first, then run:
    mpremote connect COM4 fs mkdir :lib
    mpremote connect COM4 fs cp OpenCTDKd_multispectral/lib/ds3231.py :lib/ds3231.py
    mpremote connect COM4 run OpenCTDKd_multispectral/rtc_test.py
"""

from machine import I2C, Pin
from lib.ds3231 import DS3231

_SDA_PIN = 4
_SCL_PIN = 5
_I2C_FREQ = 100_000
_DS3231_ADDR = 0x68


def _fmt(dt):
    y, mo, d, h, mi, s, _ = dt
    return f"{y:04d}-{mo:02d}-{d:02d}  {h:02d}:{mi:02d}:{s:02d}"


def _prompt_set_time(rtc):
    print("\nEnter new date/time (Ctrl-C or blank year to cancel):")
    try:
        raw = input("  Year   (e.g. 2026): ").strip()
        if not raw:
            print("Cancelled.")
            return
        year   = int(raw)
        month  = int(input("  Month  (1–12):      ").strip())
        day    = int(input("  Day    (1–31):      ").strip())
        hour   = int(input("  Hour   (0–23):      ").strip())
        minute = int(input("  Minute (0–59):      ").strip())
        second = int(input("  Second (0–59, Enter=0): ").strip() or "0")
    except (ValueError, KeyboardInterrupt):
        print("Cancelled.")
        return

    rtc.set_datetime(year, month, day, hour, minute, second)
    print("Time set —", _fmt(rtc.get_datetime()))


def main():
    i2c = I2C(0, sda=Pin(_SDA_PIN), scl=Pin(_SCL_PIN), freq=_I2C_FREQ)

    # Scan I2C bus and confirm DS3231 is present
    found = i2c.scan()
    print("I2C scan:", [hex(a) for a in found])

    if _DS3231_ADDR not in found:
        print(f"ERROR: DS3231 not found at 0x{_DS3231_ADDR:02X} — check wiring and power.")
        return

    rtc = DS3231(i2c)

    dt = rtc.get_datetime()
    print(f"\nRTC time:  {_fmt(dt)}")
    print(f"RTC temp:  {rtc.temperature():.2f} \u00b0C")

    print("\n[s] set time   [r] read time   [q] quit")
    while True:
        try:
            cmd = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if cmd == "s":
            _prompt_set_time(rtc)
        elif cmd == "r":
            dt = rtc.get_datetime()
            print(f"RTC time:  {_fmt(dt)}")
            print(f"RTC temp:  {rtc.temperature():.2f} \u00b0C")
        elif cmd == "q":
            break
        else:
            print("[s] set time   [r] read time   [q] quit")

    print("Done.")


main()
