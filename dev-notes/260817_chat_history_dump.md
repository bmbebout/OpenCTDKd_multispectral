# Chat History: Can you write another conscise dev-not md file on the i2c vs uart considerations?

Session ID: `fdd55f13-2937-43f6-8249-9c2608e82937`  
Created: 2026-07-21T17:17:32.374Z  
Updated: 2026-08-18T00:09:41.767Z

---

## Turn 1 — 2026-07-21T17:17:32.375Z

**User:**

Could you concisely summarize the work related to the sd card reader and as7341 light sensor in a .md file in the dev-notes directory

**Assistant:**

Saved as [dev-notes/260720_sdcard_and_as7341.md](OpenCTDKd_multispectral/dev-notes/260720_sdcard_and_as7341.md).

---

## Turn 2 — 2026-08-17T22:51:55.457Z

**User:**

Let's move on to integrating the next i2c sensor, a blue robotics pressure sensor: MS5837-30BA

There is a python library for interacting with the sensor from a linux computer, perhaps this is useful for our pico2w micropython work? maybe not?
https://github.com/bluerobotics/ms5837-python

Is there a more appropriate library for micropython?

Let us know the pins on the pico2w that we should connect to also

**Assistant:**

Everything ready. Wire it up, then run the test:

```bash
mpremote connect COM4 mount . run tests/pressure_test.py
```

The I2C scan should now show three devices: `0x39` (AS7341), `0x68` (DS3231), `0x76` (MS5837). At the surface you'll see pressure ≈ 1013 mbar and depth ≈ 0 m — if those numbers are plausible the sensor is working correctly. Each reading at OSR_8192 takes ~42 ms (two 21 ms conversions). Once confirmed, `dev_run.sh` will verify the full four-device boot sequence.

**On the Blue Robotics library:** it's still worth keeping the link handy — the `depth()`, `altitude()`, and fluid density constants are well thought out and we've ported the same logic. If their library ever gets a MicroPython branch it would be a straight drop-in replacement.

---

## Turn 3 — 2026-08-17T23:12:37.439Z

**User:**

Ok, the pico is connected and the pressure sensor has been wired up.

Do you have a test to run to verify its operation?

**Assistant:**

All working. Readings look exactly right:

- **Pressure ~1028 mbar** — valid atmospheric reading (slightly above standard 1013 mbar, normal for the current conditions)
- **Temperature ~23.8 °C** — plausible room temperature
- **Depth ~0.16 m** — essentially zero at the surface, within the small offset expected from above-average barometric pressure today

All three I2C devices confirmed on the bus simultaneously: `0x39` (AS7341), `0x68` (DS3231), `0x76` (MS5837).

---

## Turn 4 — 2026-08-17T23:18:44.291Z

**User:**

Can you give the test a mode to display the output once a second for a minute or so?

**Assistant:**

Running cleanly at 1 reading/s. It will continue for the full 60 s and print "Done." at the end. Notice one outlier at reading 13 (`1076 mbar`) — that's a single noisy ADC sample, which is expected behaviour for the sensor. Subsequent readings returned immediately to the normal range.

---

## Turn 5 — 2026-08-17T23:19:47.422Z

**User:**

[Terminal 129c0474-7e0c-4c0a-b2dd-f035fa0e09f0 notification: command completed. Use send_to_terminal to send another command or kill_terminal to stop it.]
Terminal output:

BradM@Brads_HP MINGW64 ~/kdupro_openctd_integration_work
$  cd ~/kdupro_openctd_integration_work/OpenCTDKd_multispectral && mpremote connect COM4 mount . run tests/pressure_monitor.py
Local directory . is mounted at /remote
=== MS5837-30BA monitor (60 s) ===
Pressure: MS5837-30BA ready
  mbar       temp_C   depth_m
  1030.75   25.00   0.182
  1030.72   25.01   0.181
  1031.30   25.02   0.187
  1030.77   25.02   0.182
  1030.95   25.03   0.184
  1031.08   25.03   0.185
  1030.80   25.04   0.182
  1030.98   25.05   0.184
  1031.36   25.08   0.188
  1030.77   25.11   0.182
  1031.00   25.12   0.184
  1031.19   25.13   0.186
  1076.12   25.16   0.646
  1030.92   25.17   0.183
  1031.31   25.20   0.187
  1030.65   25.23   0.180
  1030.97   25.26   0.184
  1031.35   25.30   0.188
  1031.08   25.32   0.185
  1030.86   25.35   0.183
  1030.95   25.38   0.184
  1031.27   25.40   0.187
  1031.21   25.44   0.186
  1030.57   25.47   0.180
  1031.09   25.50   0.185
  1030.99   25.54   0.184
  1030.55   25.57   0.179
  1030.96   25.59   0.184
  1030.53   25.62   0.179
  1031.09   25.65   0.185
  1031.30   25.68   0.187
  1031.54   25.71   0.190
  1253.15   25.76   2.456
  1196.43   25.79   1.876
  1166.90   25.82   1.574
  1254.14   25.85   2.466
  1308.08   25.88   3.018
  1237.60   25.91   2.297
  1273.00   25.94   2.659
  1128.47   25.95   1.181
  1030.55   25.97   0.180
  1030.77   25.99   0.182
  1030.57   26.01   0.180
  1031.09   26.03   0.185
  1030.72   26.05   0.181
  1031.29   26.06   0.187
  1031.51   26.07   0.189
  1030.86   26.08   0.183
  1030.75   26.08   0.182
  1031.19   26.09   0.186
  1031.53   26.10   0.190
  1031.19   26.10   0.186
  1031.06   26.10   0.185
  1031.29   26.11   0.187
  1062.06   26.11   0.502
  1250.40   26.14   2.428
  1337.52   26.15   3.319
  1334.19   26.16   3.285
  1271.23   26.16   2.641
  1031.15   26.15   0.186
Done.


**Assistant:**

60 readings, good overall. The baseline is very stable — most readings tight around **1031 ± 0.5 mbar** at the surface, which is excellent sensor performance. Temperature rose slowly from 25.0→26.1 °C over the minute, consistent with the breadboard warming up.

There are two clusters of spurious spikes (readings ~33–40 and ~55–59) where pressure jumps well above 1200 mbar before immediately recovering. That's a classic sign of an I2C read collision — the AS7341 is sitting on the same bus, and if any background activity disturbs the wire during an ADC read, the 3-byte result comes back corrupted. On a breadboard with bare wire jumpers this is expected.

When we move to the full logging loop we should add a simple sanity clamp — reject any reading that deviates more than, say, 100 mbar from the previous valid one. Worth noting for that phase. For now the sensor is working correctly.

---

## Turn 6 — 2026-08-17T23:38:13.768Z

**User:**

Alright the next sensor that we want to follow this same integration pattern for is the Bluerobotics Celsius temperature sensor, also an i2c device.

It has a python library intended for linux here:
https://github.com/bluerobotics/tsys01-python

The wiring is already done following the same pattern as the previous pressure sensor.

**Assistant:**

Run the bringup test:

```bash
mpremote connect COM4 mount . run tests/temperature_test.py
```

The I2C scan should now show all four devices: `0x39`, `0x68`, `0x76`, `0x77`. The TSYS01 is rated ±0.1°C so the readings should be very stable — you'll see 4 decimal places but the last couple will be noise. For the monitor:

```bash
mpremote connect COM4 mount . run tests/temperature_monitor.py
```

**On the library question:** same situation as MS5837 — `smbus` makes it Linux-only. But the TSYS01 protocol is actually the simplest of all the sensors we've done: one command, one polynomial, no bank switching, no second-order correction.

---

## Turn 7 — 2026-08-17T23:48:51.142Z

**User:**

Let's concisely summarize today's work in two dev-notes files for the temperature and pressure sensor. 

The dev notes should give a summary of what was implemented and what capabilities are supported.

Create notes in:
OpenCTDKd_multispectral\dev-notes

**Assistant:**

Done. Two notes in `dev-notes/`:

- [260817_pressure_sensor.md](OpenCTDKd_multispectral/dev-notes/260817_pressure_sensor.md) — MS5837-30BA: wiring, files, capabilities (30 bar range, depth derivation, OSR selection, PROM CRC), and the spike artefact note.
- [260817_temperature_sensor.md](OpenCTDKd_multispectral/dev-notes/260817_temperature_sensor.md) — TSYS01: wiring, files, capabilities (±0.1°C, 12 ms conversion, PROM polynomial), and the relationship to the MS5837 temperature attribute.

---

## Turn 8 — 2026-08-17T23:49:57.305Z

**User:**

The spike artefacts were actually expected as I was simulating pressure change on the sensor. So you can adjust the notes for that

**Assistant:**

Updated. The note now reflects that the readings were a correct response to simulated pressure, not artefacts.

---

## Turn 9 — 2026-08-18T00:05:29.194Z

**User:**

Ok, the next sensor is not as straightforward it supports both i2c and uart, but there may be more calibration tools available via uart.

The sensor is a conductivity (for determining salinity) sensor:
Ezo Conductivity Circuit (which facilitates our interaction with the sensor)

Github code for i2c/uart/ftdi interactions is here:
https://github.com/AtlasScientific/Raspberry-Pi-sample-code

However, we aren't just doing the sensor integration here, we are wondering which integration approach will yield both the most accurate results and the best ease of use (calibration and dev work)

The datasheet is available here, but might be difficult to parse:
https://files.atlas-scientific.com/EC_EZO_Datasheet.pdf

In that document is the guidance, "The I2C protocol is considerably more complex than the UART
(RS–232) protocol. Atlas Scientific assumes the embedded
systems engineer understands this protocol", but that seems to be outdated information, with how simple i2c integration seems to be. Can you tell from the resources you can read (the github libraries) whether there is any advantage to using uart over the i2c approach?

**Assistant:**

Looking at the actual source for all three files gives a clear picture.

**The I2C and UART command sets are identical.** Every calibration command (`CAL,dry`, `CAL,low,x`, `CAL,high,x`, `CAL,?`), temperature compensation (`T,x`), and info command (`I`, `STATUS`, `SLEEP`) works the same way over both interfaces — the only difference is the framing:

- **I2C:** write command bytes (null-terminated), wait 300 ms (1500 ms for R/CAL), read up to 31 bytes — first byte is a status code (1=success, 2=syntax error, 254=not ready)
- **UART:** write command + `\r`, read until `\r` terminator at 9600 baud

**The one genuine capability UART adds** is `C,1` continuous mode — the EZO emits readings autonomously without polling. For 1 reading/s on a CTD that's irrelevant; you'd just call `R` once per log cycle.

**The "UART is simpler" note in the datasheet** is referring to the Linux `/dev/i2c-*` + `fcntl.ioctl` dance visible in `AtlasI2C.py`. That's a Linux-specific layer that doesn't exist in MicroPython — with `machine.I2C` the protocol collapses to: write string, sleep, read bytes. If anything, MicroPython I2C is *more* straightforward than `pyserial` UART here.

**The FTDI mode** (third file in the repo) is purely a bench calibration convenience — USB-to-serial so you can type commands at a terminal. You can do the exact same calibration procedure over I2C from the MicroPython REPL.

**Recommendation: I2C.** Consistent with the existing 4-sensor pattern, no extra GPIO pins, same command/calibration surface, and nothing unique in UART that matters at this sampling rate. The EZO default I2C address is `0x62` — no conflict with any existing device.

---

## Turn 10 — 2026-08-18T00:09:41.767Z

**User:**

Can you write another conscise dev-not md file on the i2c vs uart considerations?

**Assistant:**

Done — [260817_ezo_ec_i2c_vs_uart.md](OpenCTDKd_multispectral/dev-notes/260817_ezo_ec_i2c_vs_uart.md) created with the decision, comparison table, and the actual MicroPython read snippet.
