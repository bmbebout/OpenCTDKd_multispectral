"""SPI SD card block device driver for MicroPython.

Implements AbstractBlockDev so it can be mounted with os.VfsFat.
Compatible with standard SD (SDSC) and high-capacity (SDHC/SDXC) cards.
"""

from micropython import const
import time

_CMD_TIMEOUT  = const(200)
_R1_IDLE      = const(0x01)
_R1_ILLEGAL   = const(0x04)
_TOK_DATA     = const(0xFE)
_TOK_CMD25    = const(0xFC)
_TOK_STOP     = const(0xFD)

_INIT_BAUD    = const(400_000)   # slow clock for card init
_DATA_BAUD    = const(20_000_000)


class SDCard:
    def __init__(self, spi, cs):
        self._spi = spi
        self._cs  = cs
        self._buf = bytearray(1)
        self._mvbuf = memoryview(bytearray(512))
        self._sdhc = False
        self._cs.value(1)
        self._init_card()

    # ------------------------------------------------------------------
    # Low-level SPI helpers
    # ------------------------------------------------------------------

    def _byte(self, val=0xFF):
        """Transfer one byte, return response byte."""
        self._buf[0] = val
        self._spi.write_readinto(self._buf, self._buf)
        return self._buf[0]

    def _cmd(self, cmd, arg, crc=0x01):
        """Send an SD command and return the R1 response byte."""
        self._cs.value(0)
        self._spi.write(bytes([0x40 | cmd,
                                (arg >> 24) & 0xFF,
                                (arg >> 16) & 0xFF,
                                (arg >>  8) & 0xFF,
                                 arg        & 0xFF,
                                crc]))
        # Wait for response (MSB clear = valid)
        for _ in range(_CMD_TIMEOUT):
            r = self._byte()
            if not (r & 0x80):
                return r
        return 0xFF  # timeout

    def _cmd_end(self):
        self._cs.value(1)
        self._byte()   # release bus

    def _acmd(self, cmd, arg):
        """Send an application-specific command (preceded by CMD55)."""
        self._cmd(55, 0)
        self._cmd_end()
        return self._cmd(cmd, arg)

    # ------------------------------------------------------------------
    # Card initialisation
    # ------------------------------------------------------------------

    def _init_card(self):
        # Supply ≥74 clock pulses with CS high to wake the card
        self._spi.init(baudrate=_INIT_BAUD, polarity=0, phase=0)
        self._cs.value(1)
        for _ in range(10):
            self._byte()

        # CMD0 — reset into SPI mode
        for _ in range(_CMD_TIMEOUT):
            if self._cmd(0, 0, 0x95) == _R1_IDLE:
                break
        else:
            self._cmd_end()
            raise OSError("SD: CMD0 timeout — no card or bad connection")
        self._cmd_end()

        # CMD8 — check voltage range (required for SDHC)
        r = self._cmd(8, 0x1AA, 0x87)
        if r == _R1_IDLE:
            # Read 4-byte R7 response
            tail = self._spi.read(4, 0xFF)
            if tail[3] != 0xAA:
                self._cmd_end()
                raise OSError("SD: CMD8 voltage mismatch")
            self._sdhc = True
        self._cmd_end()

        # ACMD41 — initialise card; use HCS bit if SDHC
        hcs = 0x40000000 if self._sdhc else 0
        deadline = time.ticks_ms() + 5000
        while True:
            r = self._acmd(41, hcs)
            self._cmd_end()
            if r == 0:
                break
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                raise OSError("SD: ACMD41 timeout — card not ready")
            time.sleep_ms(10)

        # CMD58 — read OCR; confirm CCS bit for SDHC
        r = self._cmd(58, 0)
        ocr = self._spi.read(4, 0xFF)
        self._cmd_end()
        if not self._sdhc:
            self._sdhc = bool(ocr[0] & 0x40)

        # CMD16 — set block length to 512 for SDSC cards
        if not self._sdhc:
            self._cmd(16, 512)
            self._cmd_end()

        # Switch to full-speed SPI
        self._spi.init(baudrate=_DATA_BAUD, polarity=0, phase=0)

    # ------------------------------------------------------------------
    # Block device interface (required by os.VfsFat)
    # ------------------------------------------------------------------

    def readblocks(self, block, buf, offset=0):
        n = len(buf) // 512
        addr = block if self._sdhc else block * 512
        if n == 1:
            self._cmd(17, addr)
            self._readblock(buf, offset)
            self._cmd_end()
        else:
            self._cmd(18, addr)
            for i in range(n):
                self._readblock(buf, offset + i * 512)
            self._cmd_end_multi()

    def writeblocks(self, block, buf, offset=0):
        n = len(buf) // 512
        addr = block if self._sdhc else block * 512
        if n == 1:
            self._cmd(24, addr)
            self._writeblock(buf, offset)
            self._cmd_end()
        else:
            self._cmd(25, addr)
            for i in range(n):
                self._writeblock_multi(buf, offset + i * 512)
            # Stop transmission token
            self._cs.value(0)
            self._byte(_TOK_STOP)
            self._wait_idle()
            self._cmd_end()

    def ioctl(self, op, arg):
        if op == 4:   # BP_IOCTL_SEC_COUNT
            self._cmd(9, 0)
            csd = self._readblock_raw()
            self._cmd_end()
            if csd[0] >> 6 == 1:   # CSD v2
                size = (((csd[7] & 0x3F) << 16) | (csd[8] << 8) | csd[9]) + 1
                return size * 1024
            c_size = ((csd[6] & 0x03) << 10) | (csd[7] << 2) | (csd[8] >> 6)
            c_mult = ((csd[9] & 0x03) << 1) | (csd[10] >> 7)
            return (c_size + 1) * (2 ** (c_mult + 2))
        if op == 5:   # BP_IOCTL_SEC_SIZE
            return 512
        if op == 6:   # BP_IOCTL_ERASE
            return 0
        return None

    # ------------------------------------------------------------------
    # Internal block read/write helpers
    # ------------------------------------------------------------------

    def _wait_token(self, token):
        deadline = time.ticks_ms() + 2000
        while True:
            b = self._byte()
            if b == token:
                return
            if b != 0xFF or time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                raise OSError(f"SD: expected token 0x{token:02X}, got 0x{b:02X}")

    def _wait_idle(self):
        deadline = time.ticks_ms() + 2000
        while self._byte() != 0xFF:
            if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
                raise OSError("SD: write timeout waiting for idle")

    def _readblock(self, buf, offset):
        self._wait_token(_TOK_DATA)
        mv = memoryview(buf)
        self._spi.readinto(mv[offset:offset + 512], 0xFF)
        self._spi.read(2, 0xFF)   # discard CRC

    def _readblock_raw(self):
        """Read a raw 16-byte block (used for CSD/CID)."""
        self._wait_token(_TOK_DATA)
        data = self._spi.read(16, 0xFF)
        self._spi.read(2, 0xFF)
        return data

    def _writeblock(self, buf, offset):
        self._byte(_TOK_DATA)
        mv = memoryview(buf)
        self._spi.write(mv[offset:offset + 512])
        self._spi.write(b'\xFF\xFF')  # dummy CRC
        r = self._byte()
        if (r & 0x1F) != 0x05:
            raise OSError(f"SD: write rejected (response 0x{r:02X})")
        self._wait_idle()

    def _writeblock_multi(self, buf, offset):
        self._byte(_TOK_CMD25)
        mv = memoryview(buf)
        self._spi.write(mv[offset:offset + 512])
        self._spi.write(b'\xFF\xFF')
        r = self._byte()
        if (r & 0x1F) != 0x05:
            raise OSError(f"SD: multi-write rejected (response 0x{r:02X})")
        self._wait_idle()

    def _cmd_end_multi(self):
        """End a CMD18 (multi-block read) with CMD12."""
        self._byte()             # stuff byte before CMD12
        self._cmd(12, 0)
        self._wait_idle()
        self._cmd_end()
