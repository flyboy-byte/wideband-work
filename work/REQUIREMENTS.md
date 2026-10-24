# Requirements — rusEFI wideband (module + carrier)

Answered by the owner from 2026-10-23. Ask one question at a time with a recommended option.

| Requirement | Answer | Notes |
| --- | --- | --- |
| What the board does | Wideband O2 (air-fuel) controller for a Bosch LSU sensor; module plus standalone carrier (from upstream README) | Intent: build and order as is first, then adapt it (owner, 2026-10-23) |
| Is a breakout board or perfboard enough? | | If yes, stop here |
| Size target, and which edge is the hard limit | | mm and inches |
| Wire edge (all field wires, battery, plugs leave one edge) | | |
| Antenna / radio / SIM end | | |
| Mounting (holes in every corner, rounded corners, nylon near antenna) | | |
| Temperature range (outdoor = -40 C on every part) | | |
| User-handled parts (terminals, SIM, buttons, battery, pigtails, programming pads) | | Each gets the 3D access check |
| Power source and rails | | |
| Programming method (pogo / Tag-Connect pads vs USB) | | |
| Assembly (top side only?) | | |
| Quantity, first batch | | |
| Ships to others? (labels, compliance) | | If yes, read `reference/compliance-and-bringup.md` |

## Risk probes asked
Functions this board has, and the probes they triggered (`reference/intent-capture.md`):
Plan (answers empty until asked):
Answers so far (2026-10-23):
- Sensor: aftermarket LSU 4.9 is fine (owner). Plan: free-air calibrate it, treat early readings as approximate.
- Receivers wanted: rusEFI (CAN), Speeduino, Honda K20Z3 + Hondata FlashPro, carburetor tuning with a dash or gauge, "generally compatible with anything" (owner).
- Finding (upstream files, not an order): module+carrier firmware (`f0_module`) sends only the rusEFI CAN format, defines no AUXOUT analog output, and the module has no analog-out pad (16 pads, two 8-pin edge connectors; corrected 2026-10-23, see `docs/analog-out.md`). Analog output exists only on the F1 boards (`f1_rev2/rev3/dual`, hardware in rusefi/rusefi-hardware, not cloned).

Probe plan:
- runs from a vehicle's 12 V -> load dump/TVS, reverse polarity, ignition-switched feed, -40..+85 C parts, connector, fuse:
- drives a sensor heater (switched load, high current) -> heater current and MOSFET thermal, what stops it driving a cold sensor:
- reads a precision analog sensor (pump cell) -> calibration method, noise, what the owner can verify without a scope:
- CAN bus -> termination, which ECU/bus it joins, ID/protocol (`wideband-can.dbc`):
- ships to others? (not stated) -> case, label: owner designs his own enclosure in CAD (2026-10-23); upstream's case.STL is not a limit

## What working means (bring-up tests, decided before layout)
Checkable with the owner's bench. Changing one later needs a dated reason in `STATE.md`.

| # | Do | Measure / observe | Pass |
| --- | --- | --- | --- |
| T1 | Unpowered, meter across each rail to GND | resistance | > 1 kOhm (no short) |
