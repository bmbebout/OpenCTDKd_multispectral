"""SD card bringup test — write and read a CSV file.

Deploy and run (uses local mount, no file copy needed):
    bash scripts/dev_run_test.sh tests/sdcard_test.py
Or:
    mpremote connect COM4 mount . run tests/sdcard_test.py
"""

import os
import lib.storage as storage

_TEST_FILE = "sdcard_test.csv"
_HEADER    = ["timestamp", "sensor", "value", "unit"]
_ROWS      = [
    ["2026-07-20 10:00:00", "RTC_temp", "27.00", "C"],
    ["2026-07-20 10:00:01", "RTC_temp", "27.25", "C"],
    ["2026-07-20 10:00:02", "RTC_temp", "27.00", "C"],
]


def main():
    print("=== SD card test ===")

    # Mount
    try:
        storage.setup()
    except OSError as e:
        print("FAIL: could not mount SD card:", e)
        return

    # List SD root
    print("SD root:", os.listdir("/sd"))

    # Clean up any leftover test file
    if storage.exists(_TEST_FILE):
        os.remove("/sd/" + _TEST_FILE)
        print("Removed existing", _TEST_FILE)

    # Write header + rows
    storage.append_csv(_TEST_FILE, _HEADER)
    for row in _ROWS:
        storage.append_csv(_TEST_FILE, row)
    print(f"Wrote {1 + len(_ROWS)} rows to {_TEST_FILE}")

    # Read back and verify
    contents = storage.read_file(_TEST_FILE)
    lines = contents.strip().splitlines()
    print(f"\nRead back {len(lines)} lines:")
    for line in lines:
        print(" ", line)

    # Verify row count
    expected = 1 + len(_ROWS)
    if len(lines) == expected:
        print(f"\nPASS: {expected} lines verified")
    else:
        print(f"\nFAIL: expected {expected} lines, got {len(lines)}")


main()
