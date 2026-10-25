# Findings: Astra review / Codex, 2026-10-25 — round 6

Reviewed: `e0b802a5ca53d679b9fa85e5889658d3f74d6dab` on `analog-out`. Mode B, full repo (prior rounds visible, not blind).
Tools available: shell, KiCad, ngspice + locally licensed TI model, ARM compiler. No hardware. Review branch/folder dated as requested by owner.

## Verdict

Would I order these files as they are? **Not yet assessed**: review in progress; no release or hardware approval implied.

## Coverage (one row per task in TASKS.md; fill it in as you go, not at the end)

| Task | Status | Finding IDs | What I did (command, file, calculation) |
| --- | --- | --- | --- |
| TK1 Fab files | PARTLY | — | MEASURED: 26/26 BOM and 38/38 CPL rows match board and cached transforms; 6 not-fitted consistent. `TK1-rows.md`, `TK1-fab.log`, `TK1-rotation.log`. JLC machine placement preview not available. |
| TK2 Module files | OK | — | `TK2-rotation.log`: 57/57; four questions independently answered in `TK2-module.md`. Torex primary datasheet resolves U9 override; JLC preview still needed as for TK1. |
| TK3 Boot level | PARTLY | — | Digital fix checks out: primary datasheets, both board.h files, SEL1 compile guard. Worst old-pullup bound 0.575V at 3.6V including R3+1%; PWM load <0.774mA. Rail sequencing/analog reset transient not established; see TK3-boot.md. |
| TK4 Invalid output | PARTLY | — | 21/21 aux tests pass, source path table in TK4-invalid.md. Normal invalid states command5V; sensor fault detection and receiver response cannot be universalized from this logic. |
| TK5 Heater clamp | | | |
| TK6 Analog DC | | | |
| TK7 Stability | | | |
| TK8 Faults | | | |
| TK9 Op-amp supply | | | |
| TK10 Layout | | | |
| TK11 Wiring sheet | | | |
| TK12 Firmware diff | | | |
| TK13 These docs | | | |
| TK99 Beyond the list | | | |

Status: OK = checked and found right; FINDING = see the table below; PARTLY = say what is left; NOT CHECKED = say why
(no tool, no time, no file).

## Findings

| ID | Task | Severity | Location | Evidence (numbers) | Smallest fix |
| --- | --- | --- | --- | --- | --- |
| <initials>1 | TK? | <BLOCKER / BUG / RISK / NOTE> | <file:line, or ref and x/y mm> | <measured or calculated, with source> | <one change> |

Severity: BLOCKER = don't order; BUG = wrong but workable; RISK = could bite (say when); NOTE = worth knowing.
Tag each piece of evidence: MEASURED (you ran it), CALCULATED (show the sum), DOCUMENTED (name the datasheet and page),
INFERRED (your reasoning). A finding without a number or a source is a NOTE.

### Two examples of the level we want (from earlier rounds)

- **Round 4, heater (BUG):** "`heater_control.cpp`: the effective heater voltage goes negative above the target
  temperature and is then squared into a duty. Feeding the host model a sensor at 806 C gives 65 % duty, at 840 C
  100 %, so a hotter sensor gets more heat. Fix: clamp the voltage at 0 before squaring." It has a location, a run
  with numbers, and a one-line fix.
- **Round 5, boot level (BUG):** "Both `board.h` files set PB1 as an input with its pull-up on (`board.h:335`,
  `bootloader/cfg/board.h:333`); the app only hands PB1 to TIM3 in `InitAuxDac()`. Pull-up 25-55k against R3 100k
  gives 2.13-2.64 V, a high at U4, so J3-5 sits at 5.04 V for about 0.8 s at every key-on, and indefinitely in the
  bootloader. Fix: R3 to 4.7k (0.52 V worst case), and/or a pull-down in both `board.h`." It cites the lines, does
  the sum, and names the condition that makes it matter.
- Not useful: "consider adding ESD protection to the output". Where, against what, and why is what's there not enough?

## Checked and found right

### TK1

MEASURED: the independent `placement_rows.py` checks every BOM/CPL row, including value, package, LCSC field, side, position and angle arithmetic. All match. Five high-risk pad-net/transform checks are recorded in `TK1-rows.md`: D2 cathode goes to protected supply (not raw); U2 tab is GND, leads input/output, offset 0.725 mm; U4 pins 1/3 GND, 2 PWM, 4 output, 5 reference; U5 pins 1/2/3 input/reference/GND; U6 pins 1/2/3 output/negative/positive, 4 GND, 8 supply, 6/7 tied as unused follower. These match the ST L78M, Nexperia 74LVC1G125, TI REF30 and LM2904 pin conventions inspected in the earlier source review. CAD values are not proof of delivered component identity. Independent arithmetic still shares the cached footprint data with the exporter; final JLC preview is outstanding. No definite reversed part found.

### TK2

DOCUMENTED/MEASURED: U9 pinout override is correct (Torex XC6206 ETR03005-009 p3). Q1 tab/drain is board pad 2; CPL correction and shift agree with the footprint fit. R10 keeps 61.9 ohm and improves initial tolerance; C3 is the 33 nF feedback capacitor in parallel with R33 10k, not a bypass cap. See `TK2-module.md` for calculations and primary sources.

### TK3

DOCUMENTED/CALCULATED: R3's digital low margin is adequate, PB1 is not read as a strap in this build, and PWM drive current is small relative to the specified GPIO capability. Bootloader/update/no-valid-app all retain the low command. That is a steady command guarantee, not proof that the connector is 0V during every supply ramp or immediately after a reset from full scale. `TK3-boot.md` gives the state table and measurement needed.

### TK4

MEASURED:21 auxiliary tests pass (`TK4-aux.log`). DOCUMENTED: every failed software validity predicate overrides the curve with5V; test mode intentionally bypasses it. INFERRED:5V is a reasonable lean-side fallback for a correctly configured AFR10-20 receiver, but is indistinguishable from a real lean reading and cannot guarantee safe fueling. Physical disconnect detection latency and specific receiver policies remain bench/configuration questions. See TK4-invalid.md.

## Could not check

<what, and what you would need>

## TK13: what would have made this review faster

<missing files, unclear instructions, wrong paths>
