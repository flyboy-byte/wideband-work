# Road to a working controller (assessment, 2026-10-24)

This is where the project stands on the way to ordering, building and running it, and what is still needed. It
covers the boards, the firmware, flashing, the manufacturer, money and the bench. Claims are tagged as in `AGENTS.md`.
Prices are REPORTED, from JLC's pages and live API on 2026-10-24; re-read the quote on the day.

## Where we are

- **Carrier (our board)**: r41 layout with the B1 fix, R3 4.7k (2026-10-24).
  - 25 checks pass. The raw upstream DRC is advisory (owner decision D2).
  - The fab candidate is exported and checked part by part.
  - All 26 BOM lines are in stock at JLC for 5 boards.
  - It has had five audit rounds: Sonnet self-audit, Opus, Codex x2, and the cousin's Claude. Round 5's one BUG (B1)
    is fixed. Its RISK R1 has been simulated on TI's model; results are under "R1".
- **Module (upstream's board, rev C)**: not modified by us.
  - Its JLC files are staged in `work/out/module/` (`gen/module_fab.py`), with two BOM swaps for parts JLC can't
    supply (R10 61.9R, C3 33n). The hand-soldered headers are taken off the assembly list.
  - Rotation check done (57 parts): upstream's CPL agrees with the EasyEDA measurement on 56. Q1 (VND14NV04 heater switch,
    TO-252) needed 0 deg, not 180, so it's corrected in the staged CPL. Whether anyone built rev C from these exact
    files is UNKNOWN.
- **Firmware**: builds at 21.5 kB, with RAM full by design.
  - 70 host tests and 21 analog-output tests pass; the stack estimate fits with a 64 B margin.
  - Nothing has run on hardware yet.
- **Nothing has been ordered, flashed or built.**

## The route (each step's exit is what has to be true, not a document)

| # | Step | Exit | Who | Money |
| --- | --- | --- | --- | --- |
| 1 | Re-audit of the 2026-10-24 changes (R3 4.7k and PB1 pull-down, invalid = 5 V, heater clamp, new checks and sims) | An audit round names the current commit with no open BLOCKER or BUG (`release.py` enforces it) | Codex and/or the cousin's Claude, then Claude verifies | no |
| 2 | ~~Module pre-order check~~ done 2026-10-24 | `checks/jlc_rotation.py --board module`: 57 parts. Upstream's CPL agrees on 56; **Q1 (VND14 heater switch) would have been placed turned 180 deg**, so it's corrected in `out/module/module-cpl.csv`. U9's EasyEDA pin names are wrong; the Torex PDF is to read. Owner still reads the placement preview, Q1 first | Claude / owner (preview) | no |
| 3 | Buy the programmer and bench parts (list below) | In hand before the boards arrive | owner | ~$60-120 |
| 4 | Order carrier + module at JLC, in one cart | `release.py` released the carrier; module files from `out/module/`; order rows in `ORDERS.md` | owner | ~$170-220 for 5 + 5 (below) |
| 5 | While they ship (about 1-3 weeks, FROM MEMORY) | Flash package built and checked (`fw_package.py`); TC2030 pad-1 picture; wiring sheet with terminal numbers; bench power plan | Claude | no |
| 6 | Bring-up on the bench | T1, H1-H3 (power, flash, identity), A5 (low from reset), A1 (test steps, trim, reflash), W1 (watchdog test build), then sensor: H6, A6, A2 | owner, Claude reads the numbers | sensor |
| 7 | In the car | A4 ground offset under 20 mV, logging on FlashPro/Speeduino, CAN to rusEFI if wanted | owner | no |

## Firmware: what gets flashed, what's changed, what's open

**What gets flashed:** one combined image. It holds the bootloader (6 kB at 0x08000000) and the app with its CRC
(25,600 B at 0x08001800), and it leaves the 1 kB config page alone. It goes in through SWD on the module's Tag-Connect
pads with an ST-LINK. `python3 work/checks/fw_package.py build` stages it in `work/fw-build/<commit>/`, and `check`
validates it. The bootloader **must** be in this first flash, because B1's pull-down lives in the bootloader too.

**What's changed from upstream** (`git diff origin/master -- firmware`):

| Change | Why | Tested |
| --- | --- | --- |
| 0-5 V output on SEL_1 = PB1, TIM3_CH4, 10-20 AFR curve compiled in | the project | host, 21 tests |
| Invalid lambda -> 5.0 V (was 0 V) | fail lean, so a closed-loop ECU adds fuel (N1) | host |
| PB1 pull-down in app and bootloader `board.h` | output low from reset (B1), with R3 4.7k | `checks/boot_level.py`; bench A5 |
| Bench test mode: SEL_2 low (TEST jumper) gives 1.00/2.50/4.00 V | trim and checks with a meter | host; bench A1 |
| Trim constants, rebuilt per board after A1 | +-0.05 V endpoint target | compile-time limits |
| CAN TX never blocks 100 ms with no bus (R4) | output keeps updating with no CAN node | host F6 |
| Bootloader DATA write bounds (F1, upstream bug) | config page couldn't be overwritten by a bad update | 52 cases |
| Cortex-M0 fault handler (F9, upstream bug) | faults reached the handler instead of locking up | QEMU |
| Test-mode 16-bit time wrap (F5, ours) | steps advanced | host |
| Watchdog, 400-666 ms, kicked by the heater loop (D10) | a hung loop can't leave the heater on | host; bench W1 |
| Heater voltage clamped at 0 (upstream bug, Codex round 4) | a hot sensor got up to 100 % heater | host |

**Firmware open items**
- None of it has run on the chip. The first flash proves identity, readback and start-up (H3), and W1 proves the
  watchdog resets.
- **Trim needs a reflash per board.** After A1 you rebuild with that board's gain and offset, then flash again. So the
  SWD setup isn't a one-time thing.
- Stack high-water on the chip: the static estimate gives a 64 B margin. The real number needs a debug build on the board.
- RAM is 0 B free by design (no runtime allocation), so any future feature has to save RAM first.
- Updating over CAN later needs a rusEFI ECU or a USB-CAN adapter with rusEFI's tool. The owner's ECUs (Speeduino, K20
  FlashPro) don't speak it, so SWD is the update path (INFERRED).
- Reporting F1, F9 and the heater bug upstream is the owner's call. Upstream's own analog output (#352) is not used
  (owner).

## Manufacturer: JLCPCB, Economic assembly

**Decision: JLCPCB** (REPORTED prices 2026-10-24; reasoning INFERRED).
- The whole flow is built around JLC: LCSC part numbers, EasyEDA footprints for the measured rotation check
  (`jlc_rotation.py`), the live stock check (`bom_stock.py`) and upstream's module exports. Changing fab would throw
  that verification away.
- Economic assembly covers this exactly. Both boards are single-sided SMT with every part in stock. JLC's help pages
  (Sep 2026) give an $8 setup fee and a $1.50 stencil, plus $3 per distinct Extended part (one third-party post says
  $1.50).
- PCBWay quotes assembly per job and runs higher for simple stocked builds (third-party comparisons, REPORTED).
  OSH Park/Aisler don't place parts, and 0402 parts aren't hand-solder friendly on this bench. Neither has LCSC's
  library.
- Sources: [JLC assembly price](https://jlcpcb.com/help/article/pcb-assembly-price),
  [JLC assembly FAQ](https://jlcpcb.com/help/article/98-pcb-assembly-faqs),
  [JLC vs PCBWay vs NextPCB 2026](https://www.nextpcb.com/blog/jlcpcb-vs-pcbway-vs-nextpcb-comparison-2026).

**Cost estimate, 5 carriers + 5 modules, all assembled** (live parts prices from `checks/bom_stock.py`; PCB and
shipping FROM MEMORY):

| Item | Carrier (2-layer, 40 x 51.5) | Module (4-layer, 29 x 21) |
| --- | --- | --- |
| Bare PCBs, 5 | ~$2-7 | ~$7-20 |
| Setup + stencil | $9.50 | $9.50 |
| Extended part fees ($3 each) | 7 parts, $21 | 10 parts, $30 |
| Parts, 5 boards with attrition | $20.36 | $56.59 (STM32 $20, AD8628 $17, VND14 $10) |
| Solder joints | ~$1 | ~$2 |
| **Subtotal** | **~$55-60** | **~$105-120** |

Shipping for one cart is ~$20-35 (FROM MEMORY), and US import duty/tariff is UNKNOWN until checkout. That makes
**~$180-215 for five complete controllers**, not counting sensors. JLC can assemble just 2 of the 5 PCBs (FROM
MEMORY), which saves about $45 of parts. The setup and Extended fees stay the same, so 5 assembled costs only a
little more than 2.

## Shopping list beyond the boards (owner's money; part numbers to confirm before buying)

| What | Why | Part / note | Status |
| --- | --- | --- | --- |
| SWD programmer | first flash, trim reflash, recovery | **HiLetgo ST-Link V2 clone** (owner's pick, ~$10, FROM MEMORY); STLINK-V3MINIE is the alternative with voltage sense | D4 chosen 2026-10-24 |
| Tag-Connect cable + jumpers | the module's J2 pads to the clone | **TC2030-IDC-NL** (no legs, 6-pin 0.1" socket, 1:1 to J2; FROM MEMORY ~$40) + 4 male-to-female jumpers; wiring table in `docs/wiring.md` | to buy |
| J3 connector | carrier sensor/power/CAN/output header, hand-soldered | Molex 36783-1201 (MX120G, 12-way, right angle, -40..105 C) | DOCUMENTED ([Molex](https://www.molex.com/en-us/products/part-detail/367831201)) |
| J3 mating plug + terminals + seals | the harness side | Molex 36792-1201 (MX120G 12-circuit sealed receptacle; Newark lists it as the mate); terminals and seals per Molex AS-36783-001-001 | REPORTED, confirm terminals |
| Bosch LSU 4.9 sensor | the sensor | Bosch 0 258 017 025 or equivalent (`parts_research.md`: EUR 70-91, REPORTED) | owner |
| LSU 4.9 harness plug | sensor to harness | Bosch 1 928 404 669 (harness side) with its terminals and seals ([rusEFI wiki](https://wiki.rusefi.com/WBO/), [kit](https://www.t7design.co.uk/bosch-4-9lsu-lambda-connector-plug-pins-seals-1-928-404-669.html)). Don't cut off the sensor's own plug: it holds the trim resistor | REPORTED |
| Module-to-carrier joint, socketed (owner, 2026-10-25; round 8 OR1) | the module plugs into the carrier and lifts off for reflashing and swapping | carrier: **Mill-Max 310-43-108-41-001000** socket strip, 2 per carrier (tail 0.508 mm in the 0.762 mm holes; accepts 0.38-0.635 mm round pins; 2.79 mm insulator). Module: **Mill-Max 350-10-108-00-006000** machined pin header, 2 per module (0.457 mm head and tail; tail in the 1.0 mm holes, loose: solder it plugged into the socket so it self-aligns). Buy 6 of each (Digi-Key or Mouser; LCSC shows 0 stock). **Not** a square-pin header: 0.64 mm square is 0.905 mm across the corners and won't enter the carrier (C32713274 was wrong) | DOCUMENTED (Mill-Max data sheets, 2026-10-25) |
| Bench 12 V supply with current limit | H2: first power without the sensor, then the heater (LSU 4.9 heater up to about 2 A cold, FROM MEMORY) | a small adjustable bench supply (~$40-60), or a 12 V 3-5 A adapter with an inline fuse (INFERRED: no current limit, so H2 is less safe) | owner |
| Bung + wiring | in the car | M18x1.5 weld bung; twisted CAN pair; shielded or twisted output pair with J3-7 ground | owner |

## R1: full scale into a low-resistance receiver (TI model, clamps, R9 supply, +5V tolerance)

`sim/full_scale_corners.sh`; raw results in `sim/full_scale_corners.out`. 27 cases, all valid (DOCUMENTED, TI model;
D3/D4 use generic 1N4148 parameters, FROM MEMORY). Supply is the protected rail (battery minus about 0.4 V).

| Receiver input | +5V 4.8 V | +5V 5.0 V | +5V 5.2 V |
| --- | --- | --- | --- |
| 100k, 10k (18 cases, all supplies) | +2 mV | +2 mV | +2 mV |
| 4.7k, 13.4 V supply | -66 mV | +2 mV | +2 mV |
| 4.7k, 11.6 V supply | -87 mV | +2 mV | +2 mV |
| 4.7k, 9.0 V supply | -178 mV | -37 mV | +2 mV |

What it means:
- Into 10k or more, full scale holds within the +-0.05 V target at every corner.
- Into 4.7k, it holds while the module's +5V is at least 5.0 V and the supply at least about 11 V. With +5V at 4.8 V,
  D3 clamps the 330R/R11 node (2-3 mA into +5V) and the top of the scale drops by 0.13-0.36 AFR. 20 AFR is beyond
  anything you tune for, so the cost is at the very lean end.
- Trim can't remove this, because it depends on the load and on +5V.
- Bench check: measure +5V at bring-up (it's on J3) and the receiver's input resistance if you can. Most ECU analog
  inputs are 10k or more (INFERRED). No board change unless a 4.7k receiver is the target; lowering R11 is then the
  option, at the cost of more fault current (Codex's trade-off).

## Everything else still open (one list)

- Re-audit of the 2026-10-24 changes (step 1). Watch for a PR from the cousin; he may not be finished.
- Torex XC6206 datasheet: confirm pin 2 = VOUT (U9; EasyEDA's names say otherwise, a secondary source agrees with KiCad).
- J3 terminals and seals for the Molex 36792-1201 plug (AS-36783-001-001).
- Whether the TC2030 plug fits through the carrier cutout for the trim reflash (try with the real cable; flash the module before soldering it on).
- 2026-10-24: J3 silkscreen labels for OUT (J3-5), GND (J3-7) and 12V (J3-6, upstream's, which r1-r41 had deleted) added; wiring sheet `docs/wiring.md`.
- R9/D5 surge (Codex C6) is not simulated. Power on the 1206 resistor at the TVS clamp level was 0.44 W against a
  0.25 W rating for an unknown time (Codex, INFERRED). Owner C1: no fault-survival requirement. It stays a known RISK
  on the bench list.
- The JLC rotation *sense* is INFERRED: read the placement preview, D2 first (`docs/ordering.md`).
- Owner approvals: stage 4 fit check and stage 7 renders (status page v4).
- Bring-up tests T1, H1-H6, W1, A1-A6: none run yet (no hardware).
