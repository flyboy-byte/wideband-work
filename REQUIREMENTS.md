# Requirements — <board name>

Answered by <owner> on <YYYY-MM-DD>. Ask one question at a time with a recommended option.

| Requirement | Answer | Notes |
| --- | --- | --- |
| What the board does | | |
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
- <function> -> <probe>: <answer>

## What working means (bring-up tests, decided before layout)
Checkable with the owner's bench. Changing one later needs a dated reason in `STATE.md`.

| # | Do | Measure / observe | Pass |
| --- | --- | --- | --- |
| T1 | Unpowered, meter across each rail to GND | resistance | > 1 kOhm (no short) |
