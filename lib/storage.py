"""Storage module — SD card on SPI0 (MISO=16, CS=17, SCK=18, MOSI=19).

All path arguments are relative to the SD mount point (/sd).
Examples:  "log.csv",  "data/2026-07-20.csv"
Leading slashes are stripped automatically.

Public API:
    setup()                    -> None   mount SD at /sd; raises OSError on failure
    append_csv(path, values)   -> None   append one comma-separated row + newline
    append_log(message, timestamp) -> None append a compact UTC event to log.txt
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
_ready   = False


def setup():
    """Initialise SPI0 and mount the SD card at /sd.
    Must be called once before any other storage functions.
    Raises OSError if the card is absent or unreadable."""
    global _ready
    _ready = False
    try:
        os.umount(_MOUNT)
    except OSError:
        pass
    spi = SPI(_SPI_ID, sck=Pin(_SCK), mosi=Pin(_MOSI), miso=Pin(_MISO))
    cs  = Pin(_CS, Pin.OUT, value=1)
    try:
        sd  = SDCard(spi, cs)
        vfs = os.VfsFat(sd)
        os.mount(vfs, _MOUNT)
    except OSError:
        cs.value(1)
        raise
    _ready = True
    print(f"SD:   mounted at {_MOUNT}")


def available():
    """Return whether SD setup completed successfully."""
    return _ready


def append_csv(path, values):
    """Append one row to a CSV file on the SD card.
    Creates the file (and any needed subdirectories) if it does not exist.

    path:   file path relative to SD root, e.g. "log.csv" or "data/run1.csv"
    values: any iterable — each item is str()-converted and joined with commas."""
    full = _MOUNT + "/" + path.lstrip("/")
    row  = ",".join(str(v) for v in values) + "\n"
    try:
        with open(full, "a") as f:
            f.write(row)
    except OSError:
        _mark_unavailable()
        raise


def append_log(message, timestamp):
    """Append one timestamped UTC event to the long-running log file."""
    try:
        with open(_MOUNT + "/log.txt", "a") as f:
            f.write("%sZ %s\n" % (timestamp, message))
    except OSError:
        _mark_unavailable()
        raise


def read_file(path):
    """Return the full contents of a file on the SD card as a string.

    path: file path relative to SD root, e.g. "log.csv"
    Raises OSError if the file does not exist."""
    full = _MOUNT + "/" + path.lstrip("/")
    try:
        with open(full, "r") as f:
            return f.read()
    except OSError as e:
        errno = e.args[0] if e.args else None
        if getattr(e, "errno", errno) == 2:
            raise
        _mark_unavailable()
        raise


def exists(path):
    """Return True if path exists on the SD card, False otherwise.

    path: file or directory path relative to SD root."""
    full = _MOUNT + "/" + path.lstrip("/")
    try:
        os.stat(full)
        return True
    except OSError as e:
        # ENOENT means the requested file is absent, not that the card failed.
        errno = e.args[0] if e.args else None
        if _ready and getattr(e, "errno", errno) != 2:
            _mark_unavailable()
        return False


def _mark_unavailable():
    """Invalidate the mount after an I/O failure so callers stop using it."""
    global _ready
    _ready = False
    try:
        os.umount(_MOUNT)
    except OSError:
        pass
