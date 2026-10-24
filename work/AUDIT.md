# Audit — rusEFI wideband carrier (0-5 V analog output)

Current review: Round 3 below supersedes the historical R11/full-scale/grounding conclusions.
Independent report: `docs/codex-audit-2026-10-23.md`; board remains at `986c803`.

## Hand-off (give this to each auditor with a read-only copy; not your conclusions)
- Board: carrier PCB for the rusEFI wideband module (LSU 4.9 controller) adding a 0-5 V analog output (AFR 10 = 0 V, 20 = 5 V)
  for Speeduino / Hondata FlashPro / a gauge. Analog stage: PB1 PWM -> 74LVC1G125 on a REF3030 3.000 V -> 2x RC (3.3k/100n)
  -> LM2904 x1.68 (dual-loop feedback) -> 330R -> 1N4148WS clamps -> J3-5. Firmware: branch `analog-out`.
- Commit and files: the commit that adds this text (see `git log -1 -- work/AUDIT.md`); `hardware/board_carrier/board_carrier.kicad_{sch,pcb}`,
  `firmware/` diff (`git diff master -- firmware`), `work/docs/{analog-out,carrier,firmware}.md`, `work/sim/`.
- Changed since last audit: no independent audit has happened yet; round 1 below is the author's own self-audit (also read `RELEASE_ASSESSMENT.md`). Since then: `firmware/can_helper.cpp` drops a CAN frame instead of waiting 100 ms on this board. Earlier change (2026-10-23, run r32): the last open
  connection was closed by `gen/gen_carrier_pcb.py: close_d3_link` (D3 +5V -> U2 pin 3 on the top layer, 0.25 mm; GND via at 66.00,79.35
  tied to C1 pin 2 by 0.2 mm; C2 pin 2 given a solid pour connection).
- Check, in priority order (owner: effort goes to circuits, power, heater drive, control loops, firmware):
  1. **Analog stage from first principles**: op-amp stability with cable capacitance (`sim/stability.sh`, TI model), output
     clamps and the 0.7 mV ripple / 4.1 ms settling claim, behaviour with the output shorted to GND or +12 V.
  2. **Power**: LM2904 supply (12 V -> 1k -> 18 V zener; input TVS SMCJ30CA lets the rail reach ~35-48 V). R8 (330R) and R9 (1k)
     are 0603 (100 mW): INFERRED too small for a sustained AOUT short or a surge; not simulated.
  3. **New in r32**: C1 is the LSU heater supply bypass (upstream part). Its GND now returns through one 0.5 mm via and a 0.2 mm
     tie (was a pour connection). INFERRED fine for a bypass cap, not measured. Is a heater-drive transient a concern?
  4. **Firmware**: `git diff master -- firmware`: TIM3_CH4 on PB1 shared with the pump DAC, update from the CAN TX thread,
     0 V while lambda invalid, test mode when SEL_2 is low at power-up, RAM full to the byte.
  5. Layout of what moved; silkscreen; BOM/stock (nothing ordered; no fab files exist yet).
- Known and accepted (don't re-report): module DRC 11 and carrier DRC 22 errors that are upstream's own (`checks/drc_vs_upstream.py`
  subtracts them); upstream's thermal-relief warning on one pad; no fab files yet (nothing to compare against).
- Report format below.

Build the pack for an outside reviewer with `checks/audit_pack.py <rev> <files>` (see AGENTS.md, "Cross-model audits").

## Report format
Verdict first: "Would I order these files as they are?"

| ID | Severity | Location | Evidence (numbers) | Smallest fix | Status |
| --- | --- | --- | --- | --- | --- |

Status: open / fixed (commit) / accepted (why). `checks/release.py` refuses while a BLOCKER or BUG is open.

Severity: BLOCKER = don't order; BUG = wrong but workable; RISK = could bite (state the condition);
NOTE. Then: what was checked and found correct, and what couldn't be checked.

## Rounds
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
| C1 | RISK | R11/D3/+5V | INFERRED: 12.55 mA injection budget at 12 V fault, rail 5.5 V, assumed diode 0.6 V; no guaranteed sink established for all power states | analyze powered/unpowered fault states; qualify clamp/sink | open; O1 current limiting implemented, survival not established |
| C2 | BUG | Full-scale trim claim | INFERRED: ideal nominal maximum 4.814 V into 10k; 1% low-gain corner 4.976 V into 100k; PWM saturates at duty 1 | establish load/tolerance budget and sufficient gain headroom | open; wording qualified, electrical endpoint remains unverified |
| C3 | RISK | J3-7 sensor-ground instruction | DOCUMENTED: same net as heater return; INFERRED: main ground disconnect can divert heater return through receiver | receiver-approved grounding and fault-path analysis | open; blanket sensor-ground instruction withdrawn |
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
| C7 | RISK | PWM return path, carrier bottom strip | DOCUMENTED (pcbnew probe of r36): the 6.8 mm component is all in the strip at x 42.8-47.3, y 92.9-97.6 mm. 2.0 mm is the top-layer run over JP2 (CAN terminator, bottom) whose pads and CAN_L/CAN_TERM tracks open the bottom pour; about 4.5 mm is the two-branch layer swap to R3 and U4, where the net sits over itself. A separate 3.9 mm stretch on the bottom under the CAN pair near U3 pin 3 is not joined to it. DOCUMENTED (`auxout.cpp` `PAL_MODE_ALTERNATE(1)`): PB1 at the lowest output speed. INFERRED: the signal current is the charge of about 5-10 pF of track and buffer input (under 1 mA peak at the low speed setting, edge time from the F042 datasheet table, FROM MEMORY: 125 ns max at 50 pF); the nets beside it are VREF3 (the buffer's own supply, decoupled) and AOUT_F1 (the same PWM after the buffer, filtered by the second RC and the op-amp), and CAN is differential | none recommended; if wanted, move JP2 off the PWM corridor in the generator and re-run (one run, about 4 min) | inspected; recommend accept; owner confirms with D2 |
| F9 | BUG | `firmware/main_hardfault_asm.S`, `main.cpp` bkpt() | f0 fault entry was Thumb-2 (objdump); QEMU Cortex-M0: upstream entry and BKPT-in-handler both lock up, fixed entry reaches the C handler; no watchdog on f0 | ARMv6-M entry; no BKPT on M0, DHCSR-guarded on M3 | fixed (commit that adds this text); watchdog is owner decision D10 |

Follow-up circuit tests: ramped full-scale TI-model runs completed at protected inputs 12 V and 7.5 V:
about 5.019 V into 100k, 4.816 V into 10k. C2 remains open; typical-model headroom is adequate in these cases.
Raw results: `audit/codex-2026-10-23/full-scale-ramped.jsonl`. Conditions and resistance/fault-current tradeoff in the report.

Checked: DRC delta still 0 new/0 open; no drift before audit; small-signal stability independently reproduced.
Not checked: hardware, fault survival, BOM availability/rotation, complete firmware runtime behavior. Prior host-test result was not rerun.
