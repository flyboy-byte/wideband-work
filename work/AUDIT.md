# Audit — rusEFI wideband carrier (0-5 V analog output)

Current review: **round 6** (r41 layout + the 2026-10-24 fixes) is open for Codex and outside reviewers; start at `REVIEW.md`
(repo root). Rounds 4 (Codex) and 5 (the cousin's Claude) were at `fad8032`; their findings are answered below.
Round 3 (Codex, board r36) supersedes the historical R11/full-scale/grounding conclusions; its report is
`docs/codex-audit-2026-10-23.md`, with raw output in `audit/codex-2026-10-23/`.

## Hand-off (give this to each auditor with a read-only copy; not your conclusions)
- **The work list is `review/TASKS.md`** (TK1-TK13: question, files, how to check, what "done" means), and the
  report to fill in is `review/FINDINGS-TEMPLATE.md`. How to start, the routes and the setup: `../REVIEW.md`. This
  hand-off is the background for those tasks.
- Board: carrier PCB for the rusEFI wideband module (LSU 4.9 controller), grown to 40.0 x 51.5 mm, adding a 0-5 V analog
  output (AFR 10 = 0 V, 20 = 5 V) for Speeduino / Hondata FlashPro / a gauge.
  - Analog stage: PB1 PWM -> 4.7k pull-down R3 -> 74LVC1G125 on a REF3030 3.000 V -> 2x RC (3.3k/100n) -> LM2904 x1.68
    -> 330R -> 1N4148WS clamps -> 470R R11 -> J3-5.
  - DC feedback (68k) is taken at J3-5, after R11; 1 nF from the op-amp output for stability.
  - Firmware: branch `analog-out`.
- Commit and files: the commit that adds this text (round 6).
  - Board and schematic: `hardware/board_carrier/board_carrier.kicad_{sch,pcb}` (r41 layout, R3 4.7k).
  - Carrier fab candidate: `work/out/carrier/` (run `gen/export_fab.py`).
  - Module files: `work/out/module/` (run `gen/module_fab.py`), upstream rev C with two BOM swaps.
  - Firmware: `git diff origin/master -- firmware`.
  - Docs and sims: `work/docs/{carrier,firmware,ordering}.md`, `work/sim/*.sh`, `work/ROADMAP.md`.
- Changed since rounds 4 (Codex) and 5 (the cousin's Claude), both at r41 / `fad8032`. **Check these first:**
  1. **B1 fix.** R3 100k -> 4.7k (C25900, a Basic part). PB1 is pull-down instead of pull-up in both
     `firmware/boards/f0_module/board.h` and `bootloader/cfg/board.h`.
     - Claim: the output is low from reset until `InitAuxDac()`, even with an invalid app or during a CAN update.
     - Claim: with R3 4.7k alone (old firmware) PB1 reaches at most 0.54 V.
     - Claim: PB1 sources about 0.7 mA into 4.7k while it drives the PWM.
     - Check: the pull-down doesn't break the strap read (`port.cpp:readSelPin`, never called on SEL_1 in this build)
       or anything else on PB1. `checks/boot_level.py`.
  2. **Invalid lambda -> 5.0 V** (was 0 V), `AUXOUT_INVALID_VOLTS`. Reason: a missed fault then makes a closed-loop
     ECU add fuel. Check every path that reaches the invalid value: warm-up, the Nernst window, NaN, heater stopped.
     Check what a receiver sees in each, and what happens at the 0 V -> 5 V jump after boot.
  3. **Heater clamp** (`firmware/heater_control.cpp`, upstream code): the effective voltage is clamped at 0 before
     it's squared into a duty. Test `HeaterUpdate.HotterSensorNeverGetsMoreHeat`. Check the closed loop's behaviour
     near the clamp (integrator wind-up with the output clamped, recovery when the sensor cools).
  4. **Checker fixes** for Codex R41-CX1 (`checks/stack_estimate.py`: literal pools, unbounded indirect calls, thread
     entries) and R41-CX2 (sim wrappers fail closed). Their regression tests: `checks/test_stack_estimate.py`,
     `checks/test_sim_failures.py`. Is the stack estimate now sound for the production ELF? 15 loops through indirect
     calls are still cut (`-v` lists them).
  5. **New sim** `sim/full_scale_corners.sh`: TI model with D3/D4, the R9 supply and +5V at 4.8/5.0/5.2 V. It starts
     with `uic` because the operating point fails through R9. Is that start valid, and is 60 ms enough to settle?
  6. **Module order files**: R10 C23092 -> C2087389 (61.9R 0.1 %) and C3 C1585 -> C106862 (33n X7R). J1/J3 headers
     are taken off the BOM/CPL. Are the substitutes right for those positions in upstream's circuit?
     Module rotation check (`checks/jlc_rotation.py --board module`, new):
     - Upstream's CPL agrees on 56 of 57 parts.
     - Q1 (VND14NV04, TO-252) is corrected 180 -> 0 deg and shifted 0.91 mm (`gen/module_fab.py` CPL_FIX). Is that right?
     - U9's EasyEDA pin names are overridden (`BAD_EASYEDA_NAMES`). Check the XC6206 pinout against Torex.
     - The checker no longer folds a two-lead tab part's 180 into 0 (only true two-pad parts fit either way); the
       carrier's 38 rotations are unchanged.
  7. **Live stock check** `checks/bom_stock.py` (JLC's parts API) and the cost/route in `ROADMAP.md`.
  8. **J3 silkscreen** (bottom): J3-5 OUT, J3-7 GND, and upstream's 12V under J3-6, which r1-r41 had deleted. The labels
     are 1.0 mm; the layout is otherwise unchanged. Wiring sheet `docs/wiring.md`: J3 pins, the sensor plug, SWD.
     Does it match the board? Diagram `renders/module/swd-pads.png`: is J2 reachable through the carrier cutout?
- Still open from before:
  - The rotation *sense* of the CPL is INFERRED (JLC = KiCad). D2 (SS54) is paired by pin name.
  - R9/D5 surge is not simulated (Codex C6).
  - JLC's edge-clearance rule for assembly: C11's centre is 1.85 mm from the edge.
- Known and accepted (don't re-report):
  - Upstream's own DRC errors (module 11, carrier 23; owner decision D2).
  - No survival requirement for a 12-16 V fault on J3-5 (owner, C1).
  - Below about 1 V into a pull-up input the output reads high.
  - **R1**: full scale into a 4.7k receiver drops 66-178 mV when +5V is 4.8 V (10k and up hold within +2 mV;
    `ROADMAP.md`, bench test A7).
  - 13 small passives carry no silkscreen label.
  - Upstream's bottom text "TEST" clips a pad.
  - The watchdog covers only the heater loop.
  - The mounting holes are isolated.
  - Engine-bay temperature ratings aren't a design driver (owner).
  - Upstream's own analog output (PR #352) isn't used (owner).
- Report format: `review/FINDINGS-TEMPLATE.md` (the table below is the same, plus a Status column we fill in).
## Report format
Verdict first: "Would I order these files as they are?"

| ID | Severity | Location | Evidence (numbers) | Smallest fix | Status |
| --- | --- | --- | --- | --- | --- |

Status: open / fixed (commit) / accepted (why). `checks/release.py` refuses while a BLOCKER or BUG is open.

Severity: BLOCKER = don't order; BUG = wrong but workable; RISK = could bite (state the condition);
NOTE. Then: what was checked and found correct, and what couldn't be checked.

## Rounds
### Round 4 — 2026-10-24, Codex (independent full-repository review, r41)
Reviewed commit: `fad803240534f08eb3fbd7ce15ddc386e75148bb` (pack `8ad4b28`).
Verdict: Not yet on this round's evidence; verification defects remain, and electrical/fab coverage is explicitly incomplete. No new physical board defect established.
Raw report, tests, decks and outputs: `audit/codex-r41-2026-10-24/FINDINGS.md`.

| ID | Severity | Location | Evidence (numbers) | Smallest fix | Status |
| --- | --- | --- | --- | --- | --- |
| R41-CX1 | BUG | `checks/stack_estimate.py:83` | DOCUMENTED real ARMv6-M counterexample: 408-byte nested use on a 256-byte stack reported as 8 bytes, exit 0; indirect pointer in .text omitted | Fail unbounded indirect paths; sound target coverage plus regression | open; designer to verify |
| R41-CX2 | BUG | `sim/load_accuracy.sh:35-36` | DOCUMENTED fault injection: simulator fails all 48 cases, wrapper exits 0 with missing voltages | Require complete finite measurements and propagate any failure | open; designer to verify |

Independent circuit evidence: 10nF step 0% overshoot; 47nF step 9.238%; full-scale 4.7k case 5.00211 V with supply feed and illustrative clamps. Two other cases failed model convergence, not passed. Host suites pass 69+21 outside ptrace sandbox; all other nonadvisory configured checks return zero, but CX1 qualifies the stack result. See raw report for limits and next electrical/fab checks. No design files changed.

### Round 1 — 2026-10-23, Claude Sonnet 5.5 (self-audit, same session as the author: low independence; first written as "Claude Opus", which was wrong)
Commit: bf13162 plus the `can_helper.cpp` change in the commit that adds this text
Verdict: Not yet. Nothing found that makes the board unsafe or wrong for its main use, but R1/R2 are open RISKs, nothing has been
audited by another model, and BOM/CPL/quote do not exist. Plain-language version with confidence numbers: `RELEASE_ASSESSMENT.md`.

| ID | Severity | Location | Evidence (numbers) | Smallest fix | Status |
| --- | --- | --- | --- | --- | --- |
| R1 | RISK | R8 330R 0603 | short to +12 V: (12-5.6)/330 = 19 mA = 120 mW > 100 mW steady; short to GND 76 mW ok (INFERRED, not simulated) | R8 to 1206 | open (owner decision D1) |
| R2 | RISK | R9 1k 0603, D5 BZT52C18 | surge 35-48 V: 17-30 mA, R9 0.3-0.9 W, zener 0.3-0.5 W (INFERRED) | R9 to 1206 or accept; failure only loses the analog output | open (D1) |
| R3 | RISK | C17 to U6 pin 8 | 4.5 mm; C16 10 uF nearby; weighting the net (r33) gave 6 open connections | hand move later, or accept | accepted for now (INFERRED fine) |
| R4 | RISK | firmware, `can_helper.cpp` | no CAN node: 100 ms mailbox wait in the thread that updates the output, 100 Hz to about 9 Hz | drop the frame on this board | fixed (this commit); bench check pending |
| R5 | NOTE | REF3030 output cap | 100 nF vs REF30 table 0.1-22 uF (REPORTED) | none | accepted |
| R6 | NOTE | C1 GND return | 0.5 mm via + 0.2 mm tie instead of a pour (INFERRED fine) | none | open, for the second auditor |
| R7 | NOTE | silkscreen R3/C12, U5/C11 | overlaps | move labels | open |

Checked and found correct: stability and ripple sims reproduce the doc tables (re-run today); ERC 0; netlist 17/17; DRC vs upstream
0 new / 0 open; via-in-pad 0; firmware diff reads consistently (SEL_1 never touched as a strap, update guarded by a null config,
invalid lambda gives 0 V, build f0_module and f1_dual clean). Could not check: any hardware behaviour, clamp and pull-down in
simulation, cable inductance, temperature, BOM/stock, JLC rotation.

### Round 2 — 2026-10-23, Claude Opus 5.5 (review of round 1 and the session's work; different model, shared context: medium independence)
Commit: ebbaf34
Verdict: Not as they are. One round-1 finding (R1) had the current path wrong and the real risk is larger: a 12 V wiring fault on
J3-5 reaches the +5V rail through D3. Everything else in round 1 checks out or is a small correction.

| ID | Severity | Location | Evidence (numbers) | Smallest fix | Status |
| --- | --- | --- | --- | --- | --- |
| O1 | RISK (high consequence) | D3, `/AOUT` = J3-5, +5V rail | board file: R8 is op-amp side, D3/D4 clamp J3-5 directly. 12 V on J3-5 -> D3 -> +5V (TJA1051, REF3030, module) with no current limit; rail toward 11 V. Condition: a wiring fault, J3-6 is 12V_RAW in the same connector (INFERRED) | series resistor (e.g. 470R 1206) between the clamp node and J3-5, outside the feedback | fixed r36 (R11 470R 1206 at J3-5); replaces round-1 R1 |
| O2 | NOTE | round-1 R1, GND short | DC loop drives the op-amp high, R9 1k limits its supply: about 9 mA, R8 27 mW (round 1 said 15 mA / 76 mW) | none | fixed (text) |
| O3 | NOTE | round-1 R4 rate | `SendRusefiFormat` sends 2 frames (StandardData, DiagData), 100 ms each: about 5 Hz, not 9 Hz | none, fix already in | fixed (text) |
| O4 | NOTE | `checks/run_all.py` | summary is the last output line, which is KiCad's "Debug: Adding duplicate image handler" for via_in_pad (STATE table) | skip `: Debug: ` lines | fixed (this commit) |
| O5 | NOTE | AUDIT.md, RELEASE_ASSESSMENT.md | authorship given as Opus; written by Sonnet 5.5 | label | fixed |

Checked and found correct: the `can_helper.cpp` change (macro is live: flash +32 B after `port.h` was included; an unacked CAN frame
stays in its mailbox, so with no node all 3 fill and every later send would time out); clamp diode orientation (D3 cathode +5V,
D4 cathode `/AOUT`); R2 surge arithmetic; r33 revert left the board at bf13162 (0/0); D2 (release gate vs upstream's DRC errors) is
a real conflict in `release.py`. Not checked: anything needing hardware or a SPICE run of the fault cases.

### Design change after round 2 — r36, 2026-10-23 (not an audit round; the next auditor checks these)
Board grown 15 mm, stage moved to the new strip, R11 added. Status of earlier findings: O1/R1 fixed (R11); R3 fixed (C17
2.1 mm from U6 pin 8); R6 gone (close_d3_link no longer applies; C1 pad 2 back to upstream's own pour connection, whose
1-spoke thermal is in upstream's DRC too); R7 open (silkscreen). New for the auditor: `docs/carrier.md` "Layout review
checklist" and "Grounding and the output" (D7); `checks/layout_review.py` output; sim topology D.

### Round 3 — 2026-10-23, Codex (independent tests and source review)
Commit: 34cd49d
Verdict: Not ready to order on the existing evidence. Keep the enlarged board; resolve the electrical claims below, not enclosure dimensions.
Full evidence: `docs/codex-audit-2026-10-23.md`. Raw outputs: `audit/codex-2026-10-23/`.

| ID | Severity | Location | Evidence (numbers) | Smallest fix | Status |
| --- | --- | --- | --- | --- | --- |
| C1 | RISK | R11/D3/+5V | INFERRED: 12.55 mA injection budget at 12 V fault, rail 5.5 V, assumed diode 0.6 V; no guaranteed sink established for all power states | analyze powered/unpowered fault states; qualify clamp/sink | owner 2026-10-23: no survival requirement, accepted risk (STATE.md); was open; O1 current limiting implemented, survival not established |
| C2 | BUG | Full-scale trim claim | INFERRED: ideal nominal maximum 4.814 V into 10k; 1% low-gain corner 4.976 V into 100k; PWM saturates at duty 1 | establish load/tolerance budget and sufficient gain headroom | owner 2026-10-23: all four receivers, +-0.05 V after trim; gain headroom change to simulate next; was open; wording qualified, electrical endpoint remains unverified |
| C3 | RISK | J3-7 sensor-ground instruction | DOCUMENTED: same net as heater return; INFERRED: main ground disconnect can divert heater return through receiver | receiver-approved grounding and fault-path analysis | owner 2026-10-23: star at the ECU sensor ground; A4 measures; was open; blanket sensor-ground instruction withdrawn |
| C4 | BUG | layout_review.py | DOCUMENTED: original PWM gap 3.8 vs 4.5 mm solely from track order; now weighted component metric, all net pairs included, 3 geometry tests and 3 board orders agree | explicit sampled component metric, not a longest-path claim | fixed locally 2026-10-23; new C7 review item |
| C5 | NOTE | Stability evidence | DOCUMENTED: independent supply-fed typical-model tests settle in 176–255 us, 0–0.511% overshoot; DC attempt timed out | retain bounded result; full-scale/supply corners still needed | open (coverage limitation) |
| C6 | NOTE | LM2904 supply rating | DOCUMENTED TI SLOS068AB: plain LM2904 26 V; 32 V belongs to LM2904V | correct docs; surge-energy budget, not just larger footprint | open (generator text and surge qualification) |
| C7 | RISK | PWM ground-return corridor | DOCUMENTED repaired checker: 6.8 mm uncovered component vs existing 5 mm review trigger; not an impedance measurement | inspect corridor before routing change | inspected 2026-10-23 (Opus, below); recommend accept, board unchanged; the check still FAILs (trigger not retuned), so it joins D2 |
| F1 | BUG | f0 CAN bootloader DATA guard | DOCUMENTED source-extraction/stub test: 48 cases, 10 unsafe accepted writes (5 ordinary <=8-byte payloads, 5 synthetic length-10 cases); 26 KiB bound exceeds 25 KiB app partition; offset+length unchecked | linker-derived bounds, payload validation and production-path regressions | fixed (Claude Opus 5.5, commit that adds this text): `bootloader_bounds.h` `IsAppWriteAllowed()`, size from `__appflash_size__` (25600 in the built ELF); harness 52 cases / 0 unsafe / 0 valid refused, mutant of the old bound caught; 8 gtest cases; next auditor to re-confirm |


#### Follow-through — 2026-10-23, Claude Opus 5.5 (firmware; the next auditor re-checks these)
| ID | Severity | Location | Evidence (numbers) | Smallest fix | Status |
| --- | --- | --- | --- | --- | --- |
| F2 | NOTE | firmware package | `fw_package.py` stages and checks upstream's format; 21 good/bad package cases right; two builds byte-identical | n/a (new tooling) | done |
| F5 | BUG | `firmware/auxout.cpp` test mode | step from `TIME_I2MS(chVTGetSystemTime())`: f0 systime is 16 bits at 10 kHz, wraps at 6.55 s, step always 0 (1.00 V only); host test fails on the old code at every 2.50/4.00 V point | 64-bit `chVTGetTimeStamp()` | fixed (commit that adds this text); 16 host tests in `test/aux_out` |
| C7 | RISK | PWM return path, carrier bottom strip | DOCUMENTED (pcbnew probe of r36): the 6.8 mm component is all in the strip at x 42.8-47.3, y 92.9-97.6 mm. 2.0 mm is the top-layer run over JP2 (CAN terminator, bottom) whose pads and CAN_L/CAN_TERM tracks open the bottom pour; about 4.5 mm is the two-branch layer swap to R3 and U4, where the net sits over itself. A separate 3.9 mm stretch on the bottom under the CAN pair near U3 pin 3 is not joined to it. DOCUMENTED (`auxout.cpp` `PAL_MODE_ALTERNATE(1)`): PB1 at the lowest output speed. INFERRED: the signal current is the charge of about 5-10 pF of track and buffer input (under 1 mA peak at the low speed setting, edge time from the F042 datasheet table, FROM MEMORY: 125 ns max at 50 pF); the nets beside it are VREF3 (the buffer's own supply, decoupled) and AOUT_F1 (the same PWM after the buffer, filtered by the second RC and the op-amp), and CAN is differential | none recommended; if wanted, move JP2 off the PWM corridor in the generator and re-run (one run, about 4 min) | inspected; recommend accept; owner confirms with D2. 2026-10-24 r37 (parts on top): 4.1 mm, check passes, no waiver needed |
| F9 | BUG | `firmware/main_hardfault_asm.S`, `main.cpp` bkpt() | f0 fault entry was Thumb-2 (objdump); QEMU Cortex-M0: upstream entry and BKPT-in-handler both lock up, fixed entry reaches the C handler; no watchdog on f0 | ARMv6-M entry; no BKPT on M0, DHCSR-guarded on M3 | fixed (commit that adds this text); watchdog is owner decision D10 |

Follow-up circuit tests: ramped full-scale TI-model runs completed at protected inputs 12 V and 7.5 V:
about 5.019 V into 100k, 4.816 V into 10k. C2 remains open; typical-model headroom is adequate in these cases.
Raw results: `audit/codex-2026-10-23/full-scale-ramped.jsonl`. Conditions and resistance/fault-current tradeoff in the report.

Checked: DRC delta still 0 new/0 open; no drift before audit; small-signal stability independently reproduced.
Not checked: hardware, fault survival, BOM availability/rotation, complete firmware runtime behavior. Prior host-test result was not rerun.

### Round 4 follow-through, part 1 — 2026-10-24, Claude Opus 5.5 (designer), local only
Codex's round 4 (board r41, reviewed `fad8032`) is on its PR branch `codex/r41-independent-review` (fork PR #1), **not merged**:
the owner holds pushing and merging until the outside reviewer (the owner's cousin, his own Opus) has audited
(owner, 2026-10-24). This answers its findings on `analog-out` locally; the round's table lives on that branch.

| ID | Verified | Follow-through | Status |
| --- | --- | --- | --- |
| R41-CX1 (BUG, stack checker) | Yes: Codex's reproducer reports 8 of 256 B, exit 0, for a 408 B nested use | `checks/stack_estimate.py` reads candidate targets from `.text` literal pools too, fails an indirect call with no candidate, and excludes thread entries by their demangled names (the old exclusion compared `CanTxThread` with `CanTxThread(void*)` and never matched). Regression `checks/test_stack_estimate.py` (3 cases; the old checker gets all 3 wrong). Production f0: 22 targets, smallest margin 64 B (was 80 B), 15 loops through indirect calls still cut (listed with `-v`) | fixed locally |
| R41-CX2 (BUG, sim wrappers) | Yes: `load_accuracy.sh` printed an empty value and exited 0; `stability.sh` printed missing values as 0 | Both wrappers keep ngspice's output, require exit 0 **and** every voltage numeric, print `FAILED` per case and exit 1. A missing settling crossing prints "not found" (topology A at 10 nF, not built, had been printing 0 us). Regression `checks/test_sim_failures.py` (fake ngspice: exits 1, exits 0 without a value, partial, answers). Real runs: stability 25 cases and load accuracy 48 cases all valid, exit 0, numbers as before | fixed locally |
| Second pass (unfinished, uncommitted on Codex's branch): heater duty when the sensor runs hot | Yes, by reading upstream's code: `heater_control.cpp:187` voltage = 7.5 - PID(ESR); kP 0.3 per ohm, so about 20 C above target the voltage goes negative; `:228-230` duty = (V / Vbatt)^2 squares it back to a large positive duty; nothing clamps V at 0. Codex's run: 806 C -> 65 % duty, 840 C -> 100 % (clipped), where 0 is wanted. Bounded by the overheat stop (target + 100 C for 0.5 s -> Stopped, latched): the reading is lost, the sensor is protected (INFERRED) | Upstream code, not ours. Fix and test prepared on local branch `heater-clamp` (clamp V at 0, a host test that fails without it); **owner decides** whether it goes into our firmware and whether to report it upstream | open: owner |
| Second pass: four retried full-scale corners (10k, 4.7k at 7 V and 9 V, pull-up mid-scale) | Codex's decks (supply feed, clamp diodes, ideal 5 V) failed to converge or timed out; our `load_accuracy.sh` (fixed 12 V, no clamps) gives all 48 cases | Corners with the real supply feed and clamps remain unresolved; not interpolated | open |

### Round 5 — 2026-10-24, Claude (outside review run by the owner's cousin, sidewinderzz, on his own account)
Reviewed commit: `fad8032` (r41). Mode B (full repo); no KiCad 10 or TI model in his sandbox, so no fab-file, DRC or
TI-model checks. Raw report: `audit/claude-sidewinderzz-2026-10-24/FINDINGS.md` (from his fork's branch
`review/claude-sidewinderzz-2026-10-24`, commit kept with his authorship). He may not be finished: watch for a PR.
Verdict: "Not quite": one cheap fix first (B1).

| ID | Severity | Location | Evidence (numbers) | Smallest fix | Status |
| --- | --- | --- | --- | --- | --- |
| B1 | BUG | R3 100k with PB1, both `board.h` | PB1 pull-up (25-55k, FROM MEMORY) against R3 100k: 2.1-2.6 V, a high at the buffer: 5.04 V out for about 0.8 s per key-on, indefinitely in the bootloader | R3 4.7k and/or PB1 pull-down | **fixed** `d53bd86`: both (R3 4.7k C25900 Basic; pull-down in app and bootloader). Verified in code first (`board.h:335`, `bootloader/cfg/board.h:333`, `bootloader.cpp:251-259`). New check `checks/boot_level.py` (fails on the old configuration); bench test A5 |
| R1 | RISK | D3 clamp vs full scale into 4.7k | behavioral model: 4.836-4.935 V into 4.7k with +5V at 4.8 V | re-run on TI's model with clamps, R9 supply, +5V tolerance | **confirmed** on TI's model (`sim/full_scale_corners.sh`, 27 cases): 10k and 100k +2 mV at every corner; 4.7k -66/-87/-178 mV with +5V at 4.8 V (13.4/11.6/9 V supply), -37 mV at 9 V with +5V 5.0 V, else +2 mV. Accepted as a documented limit (receivers 10k or more meet +-0.05 V; `ROADMAP.md` R1); no board change |
| N1 | NOTE | `AUXOUT_INVALID_VOLTS` 0 V | into a pull-up, 0 V floors at 0.63-0.97 V = 11.3-11.9 AFR, a plausible rich reading | owner: keep 0 V or 5 V | **changed** to 5.0 V (owner delegated the decision, 2026-10-24): a missed fault then makes a closed-loop ECU add fuel, not pull it; host tests updated; bench test A6 |
| N2 | NOTE | supply corner text | full scale into 4.7k needs about 10 V or more | state the load with the corner | covered by `sim/full_scale_corners.sh` results |
| N3 | NOTE | toolchain | builds with gcc 13.2 too; 69 + 21 tests pass | none | noted |
