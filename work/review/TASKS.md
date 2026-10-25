# Review tasks: round 6 (carrier r41 + the 2026-10-24 fixes)

Written 2026-10-24. This is the work list for an outside reviewer. Each task has a question to answer, the files that
answer it, how to check it with a shell and without one, and what "done" means. They are in order of value: if you
run short on time or credits, the top ones matter most. Record every task in `FINDINGS.md`, even one you skipped,
so we can see what was covered.

File names are the review pack's (`INDEX.md` maps each to its repo path). With the repo, the paths are under `work/`.

**How to work** (round 4 nearly lost its best finding because it ran out of credits before writing it up):
- Start at TK1 and keep going without waiting for a reply. Nobody is watching live: the owner reads the result later
  on his phone. Ask nothing you can decide yourself; write the assumption in the finding instead.
- After each task, add its row to `FINDINGS.md`. With git, commit it on your review branch, and push if you are allowed to.
  A half-finished review that is written down is worth far more than a finished one that isn't.
- When about a quarter of your budget is left, stop starting tasks. Finish the verdict and the coverage table, commit and push.
- Going past this list is welcome (theory, circuits, anything that looks wrong). Put it under TK99.

| ID | Area | Question (answer it yes or no, with numbers) | Effort |
| --- | --- | --- | --- |
| TK1 | Fab files | Would JLC place every carrier part right: position, rotation, LCSC number, not-fitted list? | M |
| TK2 | Module files | Are the module's order files right: Q1 corrected 180 -> 0 deg, R10 and C3 substitutes, U9 pinout? | M |
| TK3 | Boot level (B1 fix) | Is J3-5 near 0 V from power-on until the app drives PB1, in every case? | S |
| TK4 | Invalid output | Does every "lambda not valid" path put out 5.0 V, and is 5 V the right failure level? | M |
| TK5 | Heater clamp | Does the clamp at 0 V hold the heater loop stable, with no wind-up or stuck state? | M |
| TK6 | Analog DC | Are the gain, full scale and accuracy right across +5V 4.8-5.2 V and the receiver loads? | M |
| TK7 | Stability | Is the dual-loop stage stable into cable capacitance, and is the sim valid? | M |
| TK8 | Faults | 12 V on J3-5, J3-5 shorted to GND, J3-1 open: what fails, and what is damaged? | S |
| TK9 | Op-amp supply | Do R9 1k and D5 18 V (the `/VOP12` rail) survive load dump behind the SMCJ24CA? | S |
| TK10 | Layout | Return paths and bypass placement of the top-side stage. | M |
| TK11 | Wiring sheet | Does `wiring.md` match the board's J3 nets and the module's SWD pads? | S |
| TK12 | Firmware diff | Anything else wrong in `firmware.diff` (watchdog, stack, test mode)? | L |
| TK13 | These docs | What was missing or unclear here, and what would have saved you time? | S |

Effort: S under 15 min, M 15-45 min, L longer (with a shell; reading-only takes about twice as long).

---

### TK1. Carrier fab files against the board

- **Why:** a part placed rotated or swapped is the most common way a first JLC order fails. JLC's preview catches
  some of it, not all.
- **Files:** `carrier-cpl.csv`, `carrier-bom.csv`, `carrier-not-fitted.csv`, `carrier-parts.txt` (positions and
  rotations from the layout), `carrier-nets.txt`, `board_carrier.kicad_pcb`, `jlc_rotation.json`, `carrier-README.md`.
- **Shell:** `python3 checks/fab_files.py` (Gerbers, BOM and CPL against the board), `python3 checks/jlc_rotation.py`
  (each part's EasyEDA footprint against our CPL). Then don't just trust them: pick the five parts most likely to be
  wrong and check them yourself.
- **Files only:** for each CPL line, find the part in `carrier-parts.txt`. The CPL is in JLC's frame: `jlc_rotation.json`
  gives each part's correction and why. Polarised and multi-pin parts first: **D2** (SS54, SMA, cathode band), **U2**
  (LM78M05, TO-252, tab = GND), U4 (74LVC1G125, SOT-353), U5 (REF3030, SOT-23), U6 (LM2904, SOIC-8): pin 1;
  D3/D4/D5.
- **Known weak spot:** the rotation *sense* (JLC = KiCad, counter-clockwise from the top) is INFERRED, not
  documented. If you can find a source that settles it, that's worth a lot.
- **Done:** every BOM line and every CPL line marked right or wrong, with the check you used.

### TK2. Module order files

- **Why:** we order upstream's module (rev C) ourselves. Upstream's CPL had Q1, the heater switch, turned 180 deg
  against EasyEDA's footprint; two upstream parts are out of stock at JLC.
- **Files:** `module-bom.csv`, `module-cpl.csv`, `module-not-fitted.csv`, `module-README.md`, `module-parts.txt`,
  `module-nets.txt`, `module-gerbers.zip`, `jlc_rotation.py`.
- **Shell:** `python3 gen/module_fab.py && python3 checks/jlc_rotation.py --board module -v`.
- **Questions:**
  - Q1 (VND14NV04, TO-252): CPL 180 -> 0 deg plus a 0.91 mm shift. Is the tab (drain/output) where the board's
    big pad is? Check it from `module-nets.txt` (Q1's pads) and the TO-252 drawing.
  - R10 C23092 -> C2087389 (61.9R 0.1 %): R10 sets the pump-current measurement. Is 0.1 % and its tempco good enough,
    and is the value the same as upstream's?
  - C3 C1585 -> C106862 (33n X7R): what does C3 do in upstream's circuit, and does X7R (against upstream's part)
    matter there?
  - U9 (XC6206P332MR, SOT-23): we believe 1 VSS, 2 VOUT, 3 VIN (upstream's KiCad footprint and CPL; Torex's page
    blocks our fetches, so UNKNOWN from the datasheet). EasyEDA's pin names disagree and are overridden. Settle it
    if you can read Torex's datasheet.
- **Done:** each of the four answered.

### TK3. Output low from reset (the B1 fix)

- **Why:** round 5 found the output went to 5 V (full lean) for about 0.8 s at power-up, before the app ran. Fix:
  R3 100k -> 4.7k to GND on the PWM line, and PB1 set to pull-down in both the app's and the bootloader's
  `board.h`.
- **Files:** `boot_level.py`, `firmware.diff` (the `board.h` hunks), `carrier-nets.txt` (`/AOUT_PWM`: R3, module
  SEL_1, U4 input), `carrier.md`.
- **Shell:** `python3 checks/boot_level.py` prints the worst-case PB1 voltage from R3 and the STM32F042's pull
  resistance range; check its numbers against the datasheet yourself.
- **Questions:** is 4.7k against the internal pull-up (worst case) below the 74LVC1G125's V_IL with margin? Does
  anything else read PB1 (`readSelPin` on SEL_1, the CAN-ID strap)? Is about 0.7 mA from PB1 into 4.7k at the
  PWM fine? What does J3-5 do while the bootloader runs, during a CAN firmware update, and with no valid app?
- **Done:** the voltage in each state, with its source.

### TK4. Invalid lambda gives 5.0 V

- **Why:** a closed-loop ECU reading a dead controller as "rich" pulls fuel and leans the engine. We chose 5 V,
  which reads as full lean, so the ECU adds fuel instead (owner delegated it; reasoning in `firmware.md`).
- **Files:** `firmware.diff` (search `AUXOUT_INVALID_VOLTS`, `auxout`), `firmware.md`.
- **Shell:** `make -C ../test/aux_out run` (21 tests); `python3 checks/host_tests.py`.
- **Questions:** list every path into the invalid value: warm-up, the Nernst window, NaN or out-of-range lambda,
  heater stopped or faulted, sensor unplugged. Do any of them put out a *valid-looking* mid-range voltage instead?
  Is 5 V the better failure level for Speeduino (EGO input), a FlashPro datalog and a gauge? Or is a level a
  receiver can tell apart from a reading better (none of the three supports a fault band, as far as we know)?
- **Done:** the path list with the output each gives, and a yes or no on 5 V.

### TK5. Heater clamp

- **Why:** round 4 found upstream's heater control squared a negative voltage into a positive duty: 65 % duty at
  806 C, 100 % at 840 C. We clamp the effective voltage at 0 before squaring.
- **Files:** `heater_control.cpp`, `firmware.diff`.
- **Shell:** `python3 checks/host_tests.py` (includes `HeaterUpdate.HotterSensorNeverGetsMoreHeat`).
- **Questions:** while the output sits at the clamp, does the PID integrator wind up, and does the loop recover
  promptly when the sensor cools? Is there an overshoot or a stuck state? Write a test if you can.
- **Done:** a yes or no with a run or a calculation.

### TK6. Analog stage, DC

- **Why:** this is the part we added. The output must read right on the receiver.
- **Files:** `carrier-nets.txt` (`/AOUT_*` nets), `board_carrier.kicad_sch`, `carrier.md` ("Receiver load and the
  feedback point"), `load_accuracy.sh`, `full_scale_corners.sh` and `.out`, `ROADMAP.md` (R1).
- **Shell:** the sims need ngspice and TI's LM2904 model (`REVIEW.md`, setup): `sim/load_accuracy.sh`,
  `sim/full_scale_corners.sh` (27 cases, about 10 min; run one sim at a time).
- **Chain:** PB1 PWM (TIM3_CH4, 46.9 kHz) -> R3 4.7k to GND -> U4 74LVC1G125 powered from U5 REF3030 (3.000 V)
  -> R4/C13, R5/C14 (3.3k/100n each) -> U6 LM2904, gain 1.68 (R6 68k, R7 100k) -> R8 330R -> D3/D4 to +5V and GND
  -> R11 470R -> J3-5. DC feedback is taken at J3-5; C15 1 nF from the op-amp output.
- **Questions:** 3.000 V x 1.68 = 5.04 V full scale: is it reachable with the LM2904's output swing from its rail
  (`/VOP12`: `/LSU_Heater+` after D2, through R9 1k, clamped by D5 18 V; so about 11-13 V at a 12-14 V battery)? Ripple at J3-5. Error into a 4.7k pull-up or pull-down receiver. Does D3 to +5V clip
  full scale when +5V is 4.8 V (R1 is accepted as a limit; is our number right)?
- **Done:** full scale, zero and ripple, with numbers.

### TK7. Stability into cable capacitance

- **Files:** `stability.sh`, `carrier.md` (stability section).
- **Shell:** `sim/stability.sh`.
- **Questions:** is the dual-loop network (DC feedback through R11 from J3-5, 1 nF local feedback) stable from 0 to
  10 nF on J3-5? TI's model is a macro-model: where would it be wrong for an LM2904? Is the step test the right test?
- **Done:** phase margin or overshoot, worst case named.

### TK8. Faults on the output

- **Files:** `carrier-nets.txt`, `carrier.md`, `wiring.md`.
- **Questions:** with 12 V on J3-5, what current flows through R11 and D3 into +5V, and can the LM78M05 (U2) rail
  absorb it? J3-5 shorted to GND: op-amp current and dissipation? J3-1 open: J3-1 and J3-7 are the same copper, so
  heater current would return through J3-7 and the receiver's ground. What would happen? Survival with 12-16 V on
  J3-5 is not a requirement (owner C1); "it doesn't burn the board or the ECU" is.
- **Done:** current and dissipation in each case.

### TK9. Op-amp supply

- **Files:** `carrier-nets.txt` (`/LSU_Heater+` -> R9 -> `/VOP12`: D5, C16, C17, U6.8), `carrier.md`, `stability.sh`.
- **Questions:** behind the SMCJ24CA, the 12 V rail can reach about 35-48 V in a surge. R9 (1k, 1206) and D5
  (18 V zener) take the difference. Power in R9 and D5 during a 400 ms load dump, and steady at 16 V? This isn't
  simulated (Codex C6). Is R9's pulse rating enough?
- **Done:** worst-case power against each part's rating.

### TK10. Layout of the top-side stage

- **Files:** `top.png`, `bottom.png`, the `iso-*.png` renders, `carrier-parts.txt`, `board_carrier.kicad_pcb`,
  `last_run.json` (layout review numbers).
- **Shell:** `python3 checks/layout_review.py -v`, `python3 checks/drc_vs_upstream.py -v`, `python3 checks/via_in_pad.py`.
- **Questions:** U4/U5/U6 bypass caps: distance to the pin and the GND via. The return path of the output current
  (J3-7 to the stage). Does the PWM trace (`/AOUT_PWM`) run near the Nernst/pump traces (`/Un`, `/Vm`, `/Ip`)?
  C11's centre is 1.85 mm from the board edge: inside JLC's assembly clearance?
- **Done:** each item OK or a finding with coordinates in mm.

### TK11. Wiring sheet

- **Files:** `wiring.md`, `carrier-nets.txt` (J3 pads), `module-nets.txt` (J2 pads), `swd-pads.png`.
- **Questions:** does each J3 row match the board's net? Do the J2 pad signals match the module's nets? Is the
  ST-Link wiring right? Does any instruction risk a wrong connection (the rule here: wiring is given by the
  silkscreen's terminal numbers, never reference designators)?
- **Done:** every row checked.

### TK12. The rest of the firmware diff

- **Files:** `firmware.diff`, `watchdog.h`, `firmware.md`.
- **Shell:** `make -C ../firmware -j8 BOARD=f0_module`, `python3 checks/stack_estimate.py -v` (15 loops through
  indirect calls are still cut), `python3 checks/run_all.py`.
- **Questions:** is the watchdog fed only from the heater loop, and is that enough? RAM is full to the byte: does
  anything allocate at run time? Is the static stack estimate sound? Test mode (SEL_2 strapped: 1/2.5/4 V steps).
- **Done:** a list of what you read, and findings.

### TK13. These review docs

Tell us what was missing, wrong or slow here. The next reviewer gets the fix.
