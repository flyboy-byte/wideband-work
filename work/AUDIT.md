# Audit — rusEFI wideband carrier (0-5 V analog output)

Current review: **round 7** (Codex/Astra, PR #3, at `18b6cef`: a re-check of the round 6 fixes) is answered below; no
open BLOCKER or BUG. The next review is planned after bench data (A1-A8). Outside reviewers start at `REVIEW.md` (repo root). Rounds 4 (Codex) and 5 (the cousin's Claude) were at `fad8032`; their findings are answered below.
Round 3 (Codex, board r36) supersedes the historical R11/full-scale/grounding conclusions; its report is
`docs/codex-audit-2026-10-23.md`, with raw output in `audit/codex-2026-10-23/`.

## Hand-off (give this to each auditor with a read-only copy; not your conclusions)
- **The work list is `review/TASKS.md`** (round 7: TK1-TK7; each with a question, files, how to check, what "done" means), and the
  report to fill in is `review/FINDINGS-TEMPLATE.md`. How to start, the routes and the setup: `../REVIEW.md`. This
  hand-off is the background for those tasks.
- Board: carrier PCB for the rusEFI wideband module (LSU 4.9 controller), grown to 40.0 x 51.5 mm, adding a 0-5 V analog
  output (AFR 10 = 0 V, 20 = 5 V) for Speeduino / Hondata FlashPro / a gauge.
  - Analog stage: PB1 PWM -> 4.7k pull-down R3 -> 74LVC1G125 on a REF3030 3.000 V -> 2x RC (3.3k/100n) -> LM2904 x1.68
    -> 330R -> 1N4148WS clamps -> 470R R11 -> J3-5.
  - DC feedback (68k) is taken at J3-5, after R11; 1 nF from the op-amp output for stability.
  - Firmware: branch `analog-out`.
- Commit and files: the commit that adds this text (round 7).
  - Board and schematic: `hardware/board_carrier/board_carrier.kicad_{sch,pcb}` (r41 layout, R3 4.7k, R9 C844867).
  - Carrier fab candidate: `work/out/carrier/` (run `gen/export_fab.py`).
  - Module files: `work/out/module/` (run `gen/module_fab.py`), upstream rev C with two BOM swaps.
  - Firmware: `git diff origin/master -- firmware`.
  - Docs and sims: `work/docs/{carrier,firmware,ordering}.md`, `work/sim/*.sh`, `work/ROADMAP.md`.
- Changed since round 6 (Codex/Astra at `e0b802a`; its report `audit/astra-2026-10-25/`, our answers in "Round 6"
  below). **Check these first** (`review/TASKS.md` TK1-TK5):
  1. **Stack checker** (R6-S6): every call loop fails now; five callers get a source-read target table (`NARROW`).
  2. **Sim wrappers** (R6-S8): `sim/completed.sh` requires the transient to reach its stop time with no abort
     message. Stability (R6-S7): step at 3 ms, with a settled-baseline guard.
  3. **R9** (R6-S3): C4410 (250 mW) -> C844867 Vishay CRCW1206 HP pulse-proof, 0.75 W, same footprint. New check
     `checks/surge_budget.py`. The layout is unchanged: one LCSC field in the board and the schematic.
  4. Backfeed (R6-S2) and C11's edge clearance (R6-S4) are accepted, with bench test A8 and the edge-rail order step.
  5. Docs: offset budget (R6-S1), fuse wording (R6-S5), stale comments, and `run_all.py --report DIR` for reviewers.
- Round 6's other conclusions stand. It found no reversed part, no open connection and no heater-control defect; U9's
  pinout is settled from Torex's datasheet. Don't redo TK1-TK13 of round 6; its PARTLY rows are TK6 here.
- Still open from before:
  - The rotation *sense* of the CPL is INFERRED (JLC = KiCad). D2 (SS54) is paired by pin name.
  - R9/D5 surge is a power budget, not a simulation (Codex C6, round 6 R6-S3).
- Known and accepted (don't re-report):
  - Upstream's own DRC errors (module 11, carrier 23; owner decision D2).
  - No survival requirement for a 12-16 V fault on J3-5 (owner, C1).
  - Backfeed into +5V from a 12 V fault on J3-5 (round 6 R6-S2, under C1; bench A8). C11 edge clearance: edge rails at the quote (R6-S4).
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
### Round 8 — 2026-10-25, Codex (Astra; ordering readiness of the released `flyboy-o2-v1`, owner-directed, no brief)
Commit: c07643c (release `a642c86`; board, firmware and generators unchanged since round 7)
Raw report: `audit/order-readiness-2026-10-25/` (PR #4, branch `review/order-readiness-2026-10-25` at `fa34127`), with
`FIRST-RUN-RECOVERY.md` and `ORDER-CHECKLIST.md`. Verdict: "No, not with the current hand-assembly shopping list."
Confirmed right: the eight frozen files match RELEASE.json; carrier Gerbers and drills equal fresh exports; module
Gerbers geometrically equal to upstream rev C; all 52 BOM lines, 95 placements and 9 not-fitted entries match the
boards; 52/52 lines in stock for 2 assemblies (parts about $34, not a quote). Verified by Claude Opus 5.5 (designer).

| ID | Severity | Location | Evidence (reviewer's) | Our check | Status |
| --- | --- | --- | --- | --- | --- |
| OR1 | BUG | carrier U3 (module footprint), `ROADMAP.md` header line | Carrier holes 0.762 mm; the named header C32713274 has 0.64 mm square pins (0.905 mm diagonal; Hanxia drawing asks for a 1.02 mm hole) | Confirmed: U3 pads drill 0.762 / pad 1.524, identical in upstream's `master` carrier (upstream's footprint, not ours). Module J1/J3 holes are 1.0 mm. sqrt(2) x 0.64 = 0.905 mm. A square-pin header can't enter the carrier | **answered, no board change** (owner chose socketed, 2026-10-25): Mill-Max 310-43-108-41-001000 sockets on the carrier (tail 0.508 mm), 350-10-108-00-006000 pins on the module (0.457 mm; within the socket's 0.38-0.635 mm), from Mill-Max's data sheets. No carrier part within 0.5 mm of either socket strip (checked from the board). `ROADMAP.md` corrected |
| OR2 | RISK | module J2 (Tag-Connect pads) / carrier cutout | Cutout 7.874 x 5.334 mm (footprint Edge.Cuts); TC2030-IDC-NL body 9.906 x 6.096 mm: it can't enter; reach from outside unproven | Cutout confirmed from the footprint (1.524-9.398 x 1.905-7.239 mm). Cable size from the reviewer (DOCUMENTED, Tag-Connect sheet 2; not rechecked) | **answered**: the module comes off. First flash on the bare module before any pins are fitted (nothing in the way). After the pins go on, the cable nose (9.906 mm long, centred on J2 at x 88.27) reaches x 83.32, while the J3-side pin strip on the module's underside spans 81.53-84.07: about 0.75 mm overlap (INFERRED from both drawings), so the cable may not seat. Reflash route then: five fine wires (3V3, SWDIO, SWCLK, nRESET, GND) tacked to the J2 pads after the first flash, glued down, to a small header (`docs/wiring.md`) |
| OR3 | NOTE | `docs/ordering.md`, fab README, HANDOFF | Old pointers to candidate files, 5-board stock check and old prices; quantity is now 2 | Confirmed | open: update with the OR1 answer |
| OR4 | RISK | first power-up | No current-limited source specified; a destructive first-power fault isn't covered by bare spares under one-order-only | Agreed; the owner has no bench supply | open: first-power source and stop values before energizing |

### Round 7 — 2026-10-25, Codex (Astra; a re-check of the round 6 fixes at `18b6cef`)
Commit: 18b6cef (board, firmware and generators unchanged since; later commits changed notes and check scripts only)
Raw report: `audit/astra-2026-10-25b/` (PR #3, branch `review/astra-2026-10-25b` at `dac8653`). Mode B, own worktree,
no designer files changed. Coverage TK1-TK7 filled; TK99 not checked (targeted round). Verdict: "Yes for a supervised
first prototype, after the existing order-day rail/placement checks; not as a qualified automotive/fault-survival
product." No BLOCKER or BUG. Verified by Claude Opus 5.5 (designer), 2026-10-25.

Confirmed right: the stack checker (four regressions, all 40 indirect-call sites, worst thread margin 92 B reproduced on
a fresh ELF), the sim wrappers (26 fake-failure verdicts, the old abort logs rejected, stability 25/25 rerun), the R9
part in board and BOM with unchanged geometry, 26/26 BOM lines in stock, 26 checks with reviewer reports kept apart. It
added 19 ASan/UBSan cases on the real f0 sampler and heater (an ESR fault invalidates the reading in 526-576 ms).

| ID | Severity | Location | Evidence (reviewer's) | Our check | Status |
| --- | --- | --- | --- | --- | --- |
| R7-S1 | RISK | `checks/surge_budget.py`; R9/D5/D1 | R9 0.480 W with a -1 % part; its 0.75 W needs Rth <= 110 K/W (Vishay 20043 note 3). D5 0.382 W is within its derated rating only below 92.7 C case (MDD BZT52 fig. 1). 38.9 V is the SMCJ24CA clamp at a 10/1000 us pulse, not a 400 ms dump | Same sums (checker rerun: 0.480 W, 0.382 W, 93 C). Agreed it is a conditional budget; no part change asked | **fixed in the wording**: the checker uses the -1 % R9 and prints both thermal conditions; `carrier.md` says "conditional budget, not load-dump qualification". Engine-bay qualification is not a requirement (do-not-re-raise), and a failure there loses only the analog output |
| R7-S2 | NOTE | `review/TASKS.md` TK4, `carrier.md` A8, this file R6-S2 | U6.8 is VOP12, not +5V: the LM2904 can't count as a +5V load. A8 as written measured the module branch only. Typical loads 6.2 mA plus the MCU; no guaranteed 13.6 mA floor | Confirmed from `carrier-nets.txt` (`/VOP12: ... U6.8`). Our R6-S2 answer listed the op-amp: wrong | **fixed**: load list corrected in TASKS, AUDIT R6-S2 and A8; A8 now measures the whole U2 output in reset, bootloader, CAN idle and LEDs-off states. Backfeed stays accepted under C1; no 12 V-on-J3-5 test on the owner's bench |
| R7-S3 | NOTE | `REVIEW.md`, this file's header, `docs/ordering.md:74` | Headers said round 6; REVIEW setup showed plain `run_all.py`; the swap rule let a 250 mW 1k 1206 replace R9 (0.480/0.250 = 192 %) | Confirmed | **fixed**: headers name round 7; setup shows `--report`; a swap must keep the power, pulse and thermal rating |

Not checked, and why (from its report): the real load-dump waveform and TVS energy, the board's thermal resistance,
the minimum +5V current in every state, the factory's rail plan for C11, physical unplug latency and the heater's
thermal loop. All need hardware; A8 and the bring-up tests cover the ones the owner's bench can.

### Round 6 — 2026-10-25, Codex (Astra, then 6.1 Sol in the same session; independent full-repository review of `e0b802a`)
Raw report: `audit/astra-2026-10-25/` (PR #2, branch `review/astra-2026-10-25` at `43cc114`). Mode B, prior rounds
visible. Coverage TK1-TK13 plus TK99: all rows filled. Verdict: "No, not yet as a release/order package": two checker
bugs that let a failure pass. Verified by Claude Opus 5.5 (designer), 2026-10-25; each fix has a regression that fails
on the code before it.

| ID | Severity | Location | Evidence (reviewer's) | Our check | Status |
| --- | --- | --- | --- | --- | --- |
| R6-S6 | BUG | `checks/stack_estimate.py` | A real recursion through a function pointer (108 B a level) passed as 116 of 256 B; `-v` hung | Confirmed: every loop with an indirect hop was cut as an artefact. 15 such loops in the production ELF, all from charging every virtual method to every virtual call | **fixed**: loops always fail; the five looping callers get a target set read from the source (`NARROW`, cross-checked against each caller's literal pool and the address-taken set); `-v` path guarded. `test_stack_estimate.py` case 4 (fails, hangs, on the old checker). Production now 148/256 B heater and pump, 164 sampling, worst margin 92 B (was 64 B, which counted impossible paths) |
| R6-S8 | BUG | `sim/full_scale_corners.sh` | ngspice aborts part-way, exits 0, prints finite zeros; the wrapper passed 27 injected cases | Confirmed, and wider: all three wrappers passed it (9 wrong verdicts in the new fake cases against the old wrappers) | **fixed**: `sim/completed.sh`: each deck prints its last time point; a run passes only if it reached the stop time and printed no abort message. `test_sim_failures.py` adds aborted-with-zeros, stopped-short, no END line, and full_scale_corners.sh. Real runs with TI's model: stability 25/25, load accuracy 48/48, full scale 27/27 pass with the check, full scale identical to the committed results |
| R6-S3 | RISK | R9 C4410 / D5 C173425 | 38.9 V for 400 ms: R9 0.437 W against 0.25 W nominal; no pulse data | Agreed. Worst case with the zener's low end (17.1 V): 0.475 W in R9, 190 % of its rating; D5 0.378 W of 0.5 W | **fixed**: R9 -> C844867 Vishay CRCW12061K00FKEAHP (pulse-proof HP, 0.75 W, same 1206 footprint; JLC 15,000, Extended, $0.55). R9 63 %, D5 76 % of rating. New check `checks/surge_budget.py` (fails on C4410). Layout unchanged: one LCSC field in the board and schematic. D5 temperature derating not modelled (NOTE) |
| R6-S2 | RISK | D3 / +5V | 12 V on J3-5: 13.6 mA into +5V; the LM78M05 can't sink | Same sum: (12 - 5 - 0.6) / 470 = 13.6 mA. The rail rises only if the board's own +5V load is below 13.6 mA (module, CAN transceiver, REF3030; UNKNOWN measured, and typical figures alone don't put it above 13.6 mA in reset or idle. Corrected in round 7, R7-S2: the op-amp is on VOP12, not +5V). Off-board receiver into an unpowered board: a pull-up of 4.7k or more to 5 V puts under 1 mA into the rail (INFERRED) | **accepted** (owner C1: no survival requirement for 12-16 V on J3-5). Bench: measure the +5V load current at bring-up (A3 step) to put a number on it |
| R6-S4 | RISK | C11 (50.4, 104.4 mm) | Body about 1.60 mm from the edge; JLC's terms ask 2.5 mm | Agreed (centre 1.85 mm, measured before). JLC's figure REPORTED by the reviewer | **accepted with an order step**: edge rails at the quote (`docs/ordering.md`, step 3); owner at the quote |
| R6-S1 | NOTE | `docs/carrier.md` | TI SLOS068: LM2904 offset 3 typ / 7 max at 25 C / 10 mV over temperature, not "up to 3 mV" | Agreed: 11.8 mV at the output at 25 C, 16.8 mV over temperature | **fixed** in the budget (trim removes the initial part; drift stays) |
| R6-S5 | NOTE | `docs/wiring.md` | The J3-7 fuse "opens before the ECU is damaged" has no I2t or receiver data | Agreed | **fixed**: now "an idea, not checked; rely on the J3-1 crimp" |
| R6-S7 | NOTE | `sim/stability.sh` | Step at 400 us came before the output settled (10 nF: 1.7532 V before, 1.6823 V settled); 100 nF overshoot 28.0 % vs 22.8 % settled | Agreed | **fixed**: step at 3 ms; the case fails if the level drifts more than 0.5 mV in the 0.3-0.5 ms before the step. Rerun (`sim/stability.out`): 25/25 settled; as built (E) 0 % to 10 nF, 9.2 % at 47 nF, 22.4 % at 100 nF; no conclusion changes |

Also from TK2 and TK13, verified and done:
- U9 (XC6206, SOT-23) pinout: the reviewer read Torex's datasheet (ETR03005-009 p3): 1 VSS, 2 VOUT, 3 VIN, as our
  override says (REPORTED, Torex via the reviewer; we couldn't fetch it). Closes the open U9 item.
- Stale text: CLAUDE.md and RELEASE_ASSESSMENT.md said 35-48 V (that was the SMCJ30CA): now 27-39 V. Comments in
  `test/aux_out/test_aux_out.cpp` (invalid = 5.0 V, not 0 V) and `firmware/can_helper.cpp` (about 5 Hz, two frames a
  cycle, not 9 Hz) fixed; the firmware's behaviour is unchanged.
- `run_all.py --report DIR`: a reviewer's run no longer rewrites STATE.md, `checks/last_run.json` or `checks/out/`.
- REVIEW.md setup now names `sim/.spiceinit` (`ngbehavior=psa`, needed by TI's model outside `sim/`).
- Not acted on: `watchdog.h` timeout arithmetic omits RLR + 1 (625 vs 626 counts, under 0.2 %, NOTE); the watchdog
  covers only the heater loop (known and accepted).

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
