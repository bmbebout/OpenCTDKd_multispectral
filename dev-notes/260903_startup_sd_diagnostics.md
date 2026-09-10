# Startup and SD Card Diagnostics

**Date:** 2026-09-03

## Symptoms

After some power cycles, the Pico reported:

```text
SD error: SD: ACMD41 timeout — card not ready
```

The web server then appeared unavailable because the original boot path stopped before starting the access point. The dashboard also reported a file-fetch error when the SD card was not mounted.

## Diagnostics

- Confirmed the SD wiring and SPI assignment:
  - MISO GPIO16
  - CS GPIO17
  - SCK GPIO18
  - MOSI GPIO19
  - 3.3 V and common ground
- Confirmed the failure occurred during SD initialization, specifically while waiting for `ACMD41` to leave idle state.
- Updated boot logic to retry SD initialization three times and continue starting the access point if the card remains unavailable.
- Added SD readiness reporting and explicit HTTP 503 responses for file operations when the card is not mounted.
- Ran the standalone SD bring-up test independently of the web server.

## Result

The standalone test subsequently passed:

- SD mounted at `/sd`
- Existing recording files were listed
- CSV write/read verification passed
- Normal firmware boot completed with the AP and web server active

This indicates the storage and web-server code are functioning. The original issue was intermittent SD initialization rather than a persistent software or filesystem failure.

## Remaining suspicion

A marginal power-up or physical connection remains possible: loose wiring, card/adapter contact, 3.3 V supply dip, adapter startup timing, or card compatibility. Reseating the card and wiring, power-cycling several times, and testing a known-good FAT32 card are the next hardware checks if `ACMD41` timeouts recur.
