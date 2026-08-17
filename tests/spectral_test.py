"""AS7341 spectral sensor bringup test — reads all 10 channels once.

Wiring (I2C0, shared with RTC):
    AS7341 VIN  → Pico 3.3V  (pin 36)
    AS7341 GND  → Pico GND   (pin 38)
    AS7341 SDA  → GPIO4      (pin 6)
    AS7341 SCL  → GPIO5      (pin 7)

Run:
    mpremote connect COM4 mount . run tests/spectral_test.py
"""

from machine import I2C, Pin
import lib.spectral as spectral

def main():
    print("=== AS7341 spectral test ===")

    # Setup — also prints I2C scan to confirm 0x39 and 0x68 (RTC) are present
    i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=100_000)
    print("I2C scan:", [hex(a) for a in i2c.scan()])

    try:
        sensor = spectral.setup()
    except OSError as e:
        print("FAIL:", e)
        return

    print("\nReading all 10 channels (two SMUX passes)...")
    ch = spectral.read_channels(sensor)

    print("\n  Channel      Counts")
    print("  -----------  ------")
    for name in spectral.CHANNEL_NAMES:
        print(f"  {name:<12} {ch[name]:>6}")

    print("\nPASS: all channels read successfully")

main()
