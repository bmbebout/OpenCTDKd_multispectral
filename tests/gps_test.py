"""GPS bring-up test for the GY-GPS6MU2 on UART1.

Wiring:
    GPS VCC -> Pico 3V3 OUT (physical pin 36)
    GPS GND -> Pico GND (physical pin 38)
    GPS TX  -> Pico GPIO9 / UART1 RX (physical pin 12)
    GPS RX  -> Pico GPIO8 / UART1 TX (physical pin 11)

Run with:
    mpremote connect COM4 mount . run tests/gps_test.py
"""

import time
import lib.gps as gps


def main():
    receiver = gps.setup()
    print("Waiting for GPS fix (up to 60 seconds)...")
    deadline = time.ticks_add(time.ticks_ms(), 60000)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        data = gps.read(receiver)
        if data["fix"]:
            print("PASS: fix")
            print("  latitude:", data["latitude"])
            print("  longitude:", data["longitude"])
            print("  altitude_m:", data["altitude_m"])
            print("  satellites:", data["satellites"])
            print("  utc:", data["utc"])
            return
        time.sleep_ms(1000)
    print("NO FIX: check antenna, sky view, wiring, and power")


main()