"""Storage module — SD card on SPI0 (MISO=16, CS=17, SCK=18, MOSI=19).

All path arguments are relative to the SD mount point (/sd).
Examples:  "log.csv",  "data/2026-07-20.csv"
Leading slashes are stripped automatically.

Public API:
    setup()                    -> None   mount SD at /sd; raises OSError on failure
    append_csv(path, values)   -> None   append one comma-separated row + newline
    read_file(path)            -> str    full contents of a file as a string
    exists(path)               -> bool   True if the path exists on the SD card
"""

import os
from machine import SPI, Pin
from lib.sdcard import SDCard

_SPI_ID  = 0
_MISO    = 16
_CS      = 17
_SCK     = 18
_MOSI    = 19
_MOUNT   = "/sd"


def setup():
    """Initialise SPI0 and mount the SD card at /sd.
    Must be called once before any other storage functions.
    Raises OSError if the card is absent or unreadable."""
    spi = SPI(_SPI_ID, sck=Pin(_SCK), mosi=Pin(_MOSI), miso=Pin(_MISO))
    cs  = Pin(_CS, Pin.OUT, value=1)
    sd  = SDCard(spi, cs)
    vfs = os.VfsFat(sd)
    os.mount(vfs, _MOUNT)
    print(f"SD:   mounted at {_MOUNT}")


def append_csv(path, values):
    """Append one row to a CSV file on the SD card.
    Creates the file (and any needed subdirectories) if it does not exist.

    path:   file path relative to SD root, e.g. "log.csv" or "data/run1.csv"
    values: any iterable — each item is str()-converted and joined with commas."""
    full = _MOUNT + "/" + path.lstrip("/")
    row  = ",".join(str(v) for v in values) + "\n"
    with open(full, "a") as f:
        f.write(row)


def read_file(path):
    """Return the full contents of a file on the SD card as a string.

    path: file path relative to SD root, e.g. "log.csv"
    Raises OSError if the file does not exist."""
    full = _MOUNT + "/" + path.lstrip("/")
    with open(full, "r") as f:
        return f.read()


def exists(path):
    """Return True if path exists on the SD card, False otherwise.

    path: file or directory path relative to SD root."""
    full = _MOUNT + "/" + path.lstrip("/")
    try:
        os.stat(full)
        return True
    except OSError:
        return False
