# STATE — rusEFI wideband (module + carrier)

Status: 2026-10-24 — board r41, fab candidate in work/out/carrier (rebuild with gen/export_fab.py), 20 checks: 0 failed, 2 advisory (raw upstream DRC, D2). **Ready for external review** (round 4): `REVIEW.md` at the repo root (fresh-clone setup verified the same day, blind pack or full repo, report format); pack `audit/carrier-f-2026-10-24/` from `sh checks/review_pack.sh`. Pushed 2026-10-24 (owner said so): analog-out at 8ad4b28, dotfiles 70aa5e9. Then JLC quote (owner, money), release.py. Firmware: watchdog D10 done, host 69 + aux 21. Nothing ordered or flashed.
Revision in progress: none yet   Revisions used (never reused): none by the owner. Upstream module exports are rev A, B, C (upstream's own scheme, not ours).
<If the project already names revisions its own way (v1.0.0), keep its scheme.>
Review pages: status report https://claude.ai/artifact/YRsjXKGZKG5AFbwkcMuYZ4 (private; rebuilt by `checks/report.py`)  fit check <link>  audit <link>

## Stages
Mark a stage done only when its exit condition is true. Strike through, don't delete.

| # | Stage | Exit condition | Done |
| --- | --- | --- | --- |
| 1 | Requirements | `REQUIREMENTS.md` answered by the owner; breakout/perfboard ruled out | |
| 2 | Parts | Every part in `parts_research.md` with pinout, land pattern, temp rating, stock, source URL; real 3D model seen for user-handled and tall parts | |
| 3 | Schematic | Generated from code; netlist self-check passes | 2026-10-24 (r41: ERC 0, self-check 18/18) |
| 4 | Fit check | Artifact page with the to-scale picture and size table (mm + in) approved by the owner | |
| 5 | Placement | Fixed parts and critical loops locked; back side checked | 2026-10-24 (r41: stage on the top, bypass caps 2.1-3.9 mm, bottom carries tracks only) |
| 6 | Routing | Best run chosen by DRC count, not router score; vias out of SMD pads | 2026-10-24 (r41: 0 new incl. fab warnings, 0 open, 0 vias in pads, layout review 0) |
| 7 | 3D and mechanical | Access check done for every user-handled part; renders looked at, then published and approved by the owner | renders looked at and published (status page v3); jumpers on open top area, holes copper-free; **owner approval pending** |
| 8 | Fab files | `checks/run_all.py` all PASS (DRC included, nothing skipped) on the current design | 2026-10-24 candidate in `work/out/carrier/`: 20 checks pass, raw upstream DRC advisory by D2 |
| 9 | Audit | `AUDIT.md` round with no open BLOCKER or BUG; earlier fixes re-confirmed | |
| 10 | Order | `checks/release.py` released `fab/<rev>/`; committed the same day; row in `ORDERS.md` | |
| 11 | Bring-up | Bring-up tests from `REQUIREMENTS.md` run and recorded below; RISK items checked; lessons in `LESSONS.md` | |

## Decisions already made (do not re-ask)
- 2026-10-23 Owner answers, asked interactively (C1-C3, D1-D11) — owner:
  - C2 receivers: all of Speeduino, K20Z3/FlashPro, an AFR gauge, and rusEFI over CAN. K20Z3 input resistance UNKNOWN: measure it at bring-up. Endpoint tolerance +-0.05 V after a one-time bench trim. Not a forced change: the shortfall (4.816 V max into 10k, Codex runs) only touches the top near 20 AFR and only into a low-resistance input. First measure the K20Z3 input with a multimeter; at 100k or more the trim reaches +-0.05 V as is; if low, simulate 68k -> about 75k or set the receiver table from measured volts (owner agreed 2026-10-23).
  - 2026-10-24 C2 build-around (owner: "build around it", no way to measure the receiver): 68k DC feedback moves to J3-5 after R11 (E). Simulated: 1-5 V within 3 mV into 4.7k-100k pull-downs and 10k-47k pull-ups; below 1 V into a pull-up still unverified. `docs/carrier.md` "Receiver load and the feedback point". In the next board run.
  - 2026-10-24 Silkscreen default (Claude, reversible; owner may override): labels at JLC's 1.0 mm / 0.15 mm minimum, only where a label clearly belongs to its part; the jumpers carry their function (TEST, 120R) instead of JP1/JP2; 13 crowded passives unlabelled (CPL and renders name them).
  - 2026-10-24 Upstream's `hardware/board_carrier/export/` files are stale (BOM 2023-01-05: SMCJ30CA/SS34, no C6-C10; positions before the 2023-02-03 re-placement). Part numbers come from the board's LCSC fields: D1 SMCJ24CA C151279, D2 SS54 C22452 (DOCUMENTED, upstream git).
  - 2026-10-24 Mounting holes isolated: no copper within 3.6 mm of H1/H2 on either layer (Claude default, r41; the owner suggested a plastic washer instead, which still works; a grounded case via plated holes would be the owner's call).
  - D9 caveat: moving the stage to the top re-places a clean board to save an unpriced fee; price the two-sided fee first and come back to the owner if the saving is small.
  - C1 12-16 V on J3-5: no survival requirement ("how bad would i have to be"); R11 470R stays as limiting only; accepted risk. Realistic route: J3-5 sits between J3-6 (12V_RAW) and J3-4 (heater+), so a solder bridge or misplug.
  - C3 grounding: star at the ECU sensor ground. J3-1 power ground to block/battery; J3-7 only to the receiver's sensor ground; A4 measures the offset.
  - D1 R9 -> 1206. D2 gate on "DRC vs upstream" instead of raw DRC, plus a dated C7 waiver. D7 no separate analog ground. D8 two M3 holes in the new bottom corners. D9 analog stage, R10 and JP2 to the top (one-sided assembly). D10 add the IWDG watchdog. D11 keep the 13 V assumption.
- 2026-10-23 No size limit from upstream's `case/case.STL`: the owner designs his own enclosure in CAD ("what case. i do cad"). The carrier may grow; not going upstream, so no compatibility to keep. Next: fit check for a larger outline (about 40 x 52 mm), analog stage to the top if it fits, D6 series resistor — owner.
- 2026-10-23 Test and audit effort goes to the big things: circuits (analog stage, power), the heater drive, the control loops (heater, pump) and firmware. Lighter checks for routine parts and docs — owner.
- 2026-10-23 No simulated-narrowband output. FlashPro use is datalogging over the 0-5 V input; stock ECU closed loop stays on its narrowband sensor — owner.
- 2026-10-23 Base stays the f0 module + a new carrier; lambda-x2 is not forked (its analog out is the same circuit). Copy its output stage, add a reference buffer and trim — owner ("keep going").
- 2026-10-23 `AGENTS.md` is the authoritative guide for all models; Codex audits follow its "Cross-model audits" section — owner asked for documentation for us, subagents and Codex.
- ~~2026-10-23 Work in a separate repo, upstream clone stays untouched~~ — replaced the same day: one repo `~/projects/wideband-work` = upstream clone + branch `analog-out` + our files in `work/`; the separate notes repo and the `rusefi-hardware` clone were deleted — owner ("combine and delete").
- 2026-10-23 Intent: build and order the upstream design as is, then adapt it — owner ("both").
- 2026-10-23 Upstream's `hardware/*/export/` files are upstream releases, not evidence of anything the owner ordered.

- 2026-10-23 Aftermarket LSU 4.9 accepted; receivers wanted: rusEFI, Speeduino, K20Z3/FlashPro, carb tuning with a dash or gauge — owner.

- 2026-10-23 Owner wants to build this board ourselves and learn from it, not buy a ready-made unit; the point is the design and testing — owner.

## Checks
<!-- checks:start -->
| Check | Result | Summary | Date | Files (sha256/12) |
| --- | --- | --- | --- | --- |
| DRC module (errors) | FAIL (advisory) | DRC 11 errors: solder_mask_bridge 10, clearance 1 (report checks/out/wideband_controller-drc.json) | 2026-10-24 | `wideband_controller.kicad_pcb` 0179d031bc63 |
| Module board identical to upstream | PASS | module board vs upstream master: 0 file(s) differ | 2026-10-24 |  |
| ERC module (errors) | PASS | ERC 0 errors (report checks/out/wideband_controller-erc.json) | 2026-10-24 | `wideband_controller.kicad_sch` e54843a1e6ef |
| DRC carrier (errors) | FAIL (advisory) | DRC 23 errors: courtyards_overlap 14, copper_edge_clearance 3, malformed_courtyard 3, starved_thermal 2 (report checks/out/board_carrier-drc.json) | 2026-10-24 | `board_carrier.kicad_pcb` 0c37ae755f3f |
| Carrier DRC vs upstream baseline (new violations, unconnected) | PASS | DRC vs upstream: 0 new violations, 0 unconnected | 2026-10-24 | `board_carrier.kicad_pcb` 0c37ae755f3f |
| Carrier: no new vias in SMD pads | PASS | via in pad: 0 new, 0 upstream | 2026-10-24 | `board_carrier.kicad_pcb` 0c37ae755f3f |
| Carrier layout review (sampled coupling and return-path heuristics) | PASS | review triggers: 0 | 2026-10-24 | `board_carrier.kicad_pcb` 0c37ae755f3f, `layout_review.py` 2dfa9e8efa14, `layout_metrics.py` 23c78d58fd8a |
| Layout geometry helper unit tests | PASS | OK | 2026-10-24 | `layout_metrics.py` 23c78d58fd8a, `test_layout_metrics.py` 2d93b205dd56 |
| Layout track-order regression | PASS | PASS: tested orders agree | 2026-10-24 | `board_carrier.kicad_pcb` 0c37ae755f3f, `layout_review.py` 2dfa9e8efa14, `layout_metrics.py` 23c78d58fd8a, `audit_layout_order.py` c40bda9f97e2 |
| ERC carrier (errors) | PASS | ERC 0 errors (report checks/out/board_carrier-erc.json) | 2026-10-24 | `board_carrier.kicad_sch` 20e09bb79f3b |
| Carrier netlist self-check (generator table) | PASS | netlist self-check: 18 nets, 0 problems | 2026-10-24 | `board_carrier.kicad_sch` 20e09bb79f3b, `gen_carrier_sch.py` a1f0542c68c5 |
| No hand edits waiting | PASS | no drift | 2026-10-24 |  |
| JLC rotation, origin and pin names from each part's EasyEDA footprint | PASS | jlc rotation: 38 parts measured, 4 need a correction, 0 problem(s) | 2026-10-24 | `board_carrier.kicad_pcb` 0c37ae755f3f, `board_carrier.kicad_sch` 20e09bb79f3b |
| Fab candidate (out/carrier) matches the board: Gerbers, BOM, CPL, not-fitted | PASS | fab files: 38 placed, 6 not fitted, outline 40.00 x 51.50 mm, 0 problem(s) | 2026-10-24 | `board_carrier.kicad_pcb` 0c37ae755f3f, `carrier-bom.csv` da46539a4b37, `carrier-cpl.csv` 66a7fdc2200c, `carrier-gerbers.zip` c24deb7ceadb |
| Firmware: bootloader DATA writes stay inside the app partition (F1) | PASS | 52 guard cases; 0 unsafe accepted writes, 0 valid writes refused (stub only) | 2026-10-24 | `bootloader.cpp` 21cbac0cd469, `bootloader_bounds.h` 72e216e2e7bc |
| Firmware: package checker accepts good images, rejects bad ones (F2) | PASS | 21 package cases, 0 wrong verdict(s) | 2026-10-24 | `fw_package.py` 34a1c5eb78dd, `wideband_image.h` 1ee39ace5944, `bootloader.cpp` 21cbac0cd469 |
| Firmware: HardFault entry reaches the C handler on a Cortex-M0 (F9, QEMU microbit) | PASS | fault entry on Cortex-M0: as expected | 2026-10-24 | `main_hardfault_asm.S` d32262764759, `main.cpp` f1c2e96ebf08 |
| Firmware: host gtest suite (sampler, heater, F7, F1 bounds, D10 watchdog) | PASS | [  PASSED  ] 69 tests. | 2026-10-24 | `heater_control.cpp` c4a69cba915d, `sampling.cpp` 8a229de01887, `watchdog.h` 3c55e521fda5, `bootloader_bounds.h` 72e216e2e7bc |
| Firmware: analog output host tests, production auxout/pump_dac/can_helper on the f0 config (F3-F6) | PASS | [  PASSED  ] 21 tests. | 2026-10-24 | `auxout.cpp` 417044786829, `pump_dac.cpp` ac1d4bf351de, `can_helper.cpp` dc0ba8d660e6, `aux_curve.h` bb88ea23e570, `wideband_board_config.h` 7c5b76b0011c |
| Firmware: static worst-case stack per thread fits (F8 estimate, f0 build) | PASS | stack estimate: ok, smallest margin 64 B | 2026-10-24 | `auxout.cpp` 417044786829, `can.cpp` 65a7078908bf, `heater_thread.cpp` 1c61085261f8, `pump_control.cpp` 6449053857fe, `sampling_thread.cpp` 65d58bbf0b52 |
| Stack checker: known-answer Cortex-M0 cases incl. a pointer in a literal pool (Codex R41-CX1) | PASS | stack checker cases: 3, 0 wrong verdict(s) | 2026-10-24 | `stack_estimate.py` 4a8fc8d65248 |
| Sim wrappers fail when ngspice gives no valid result (Codex R41-CX2) | PASS | sim wrappers: 0 wrong verdict(s) | 2026-10-24 | `stability.sh` 34e48e6b3d5a, `load_accuracy.sh` c9a8b3e9ea4e |

Written by `checks/run_all.py` at commit fad8032. Don't edit by hand.
<!-- checks:end -->

## Bring-up results
| Test | Board # | Reading | Pass? | Date |
| --- | --- | --- | --- | --- |

## Firmware tested on
| Board revision | Firmware commit | Result |
| --- | --- | --- |

## Open register (2026-10-24, end of session)
- 2026-10-24 External-review prep done: `REVIEW.md`; checks use `origin/master` when a clone has no local `master` (`checks/upstream_ref.py`); reviewers' raw output under `audit/<reviewer>-<date>/` is now tracked (packs are not); a fresh clone ran all 20 checks after building bootloader + app (stack check needs the ELF). pcb-design skill lessons added (pad pairing by pin function, fab warnings in the DRC gate, BOM from the board, independent fab-file check, outside reviewers, SPICE memory): dotfiles commit 70aa5e9, pushed 2026-10-24.
- Owner (do not re-ask): engine-bay heat is not a design driver for this prototype.
- Owner (2026-10-24, do not re-ask): no pushing or merging until the outside reviewer (his cousin's Opus) has audited; keep working locally. Upstream's own analog output (PR #352, merged 2026-10-24) is not used: we use our design (`docs/analog-out.md`).
- 2026-10-24 Codex round 4 on fork PR #1 (not merged). CX1 stack checker and CX2 sim wrappers fixed locally (`AUDIT.md`, follow-through part 1). Upstream heater bug (negative voltage squared to full duty when the sensor runs hot): fix prepared on local branch `heater-clamp`, owner decides.
- **Board/fab**: audit round 4 (Codex, plus an outside Opus reviewer via `REVIEW.md`): ~~rebuild the pack first~~ done 2026-10-24 at r41 (`checks/review_pack.sh`). ~~Push needed before an outside reviewer can clone~~ pushed 2026-10-24. JLC quote (owner): Gerbers in JLC's viewer, placement preview (D2 first), stock C13585/C14663/C15849/C7934, edge rails (C11 1.85 mm from edge), Basic 470R 1206 for R11. ~~TODO `docs/ordering.md`~~ written 2026-10-24 (quote steps, options, placement-preview list, substitution rule, APIs).
- **Module board (not prepared)**: upstream rev C exports current (2026-03-22); 4 layers, 29.0 x 20.9 mm, 60 parts; J1/J3 headers bottom (owner solders), J2 Tag-Connect pads. Run our rotation/fab checks on it.
- **Firmware**: never run on hardware; first-flash hardware unchosen (D4, money); trim needs reflash per board; watchdog heater loop only (W1); stack high-water on hardware; RAM 0 B free; F1/F9 not reported upstream (owner).
- **Deeper tests not done**: R9/D5 surge (Codex C6); 12 V on J3-5 as built (C1 accepted); supply corners: 5 V into 100k holds from 7.5 V battery up (4.34 V at 6 V); 4.7k and 7 V runs gave no result, redo; drift budget INFERRED: 60 C swing worst 40 mV at 5 V.
- **Bench**: T1, A1-A4 (A3 about 6 mA), W1, H1-H6.
- More 3D views asked for: `kicad-cli pcb render --rotate/--perspective`, next session. Status page v3 current.

## Open (older notes, 2026-10-23)
- 2026-10-23 Flashing/testing scoped in `docs/flashing-and-test-plan.md`: recommend SWD first-flash/recovery, exact probe/cable/power unchosen. Fresh native build passes 43 tests (leak check disabled due environment), not aux-output coverage. F1: bootloader DATA guard permits config-page writes; reproduced with actual guard + flash stub. Next: fix/test F1, validate image packaging, add aux-output host tests. No hardware flashing or purchases.
- 2026-10-23 Codex follow-up: layout metric repaired and regression-tested; PWM return review flag is 6.8 mm (C7). Four ramped full-scale model runs succeeded: about 5.019 V into 100k, 4.816 V into 10k, at protected supplies 12 V and 7.5 V. C1/C2/C3 remain open. Default: retain components until load/tolerance and clamp/sink behavior are jointly budgeted. 80R instead of 470R is not a standalone accuracy fix. See audit report follow-up. Long paragraph below is historical context, not current layout status.
- Analog output: `docs/analog-out.md`, `docs/carrier.md`, `docs/firmware.md`, `sim/analog_out.cir`. Firmware on branch `analog-out` builds (2026-10-23): PB1/TIM3_CH4, updated from the CAN TX thread, compiled-in 10-20 AFR curve, 0 V while invalid, full scale 5.04 V; 4.8 KB flash, 8 B RAM left; untested on hardware. Carrier analog stage proposed with parts (REF3030 C38423, 74LVC1G125 C12519, LM2904DR C7934, BAT54S C47546) and a behavioral filter simulation (0.7 mV ripple, 4.1 ms settling). Op-amp stability checked with TI's LM2904 model: feedback after the 330R oscillates; dual loop with Cf 1 nF has no overshoot from 1 pF to 47 nF (`sim/stability.sh`). Firmware test mode (SEL_2 low at power-up) and compiled-in trim added; RAM now full to the byte (no runtime allocation, so safe). Carrier schematic generated from code (`gen/gen_carrier_sch.py`, A3 sheet, upstream drawing kept): ERC 0 errors, netlist self-check 17/17 nets (2026-10-23). Carrier PCB in progress (`gen/gen_carrier_pcb.py`, 2026-10-23): new parts on the bottom (board can't grow inside `case/case.STL`; case clearance under the board about 6 mm, INFERRED); placed by an annealing placer (net length + distance to existing copper), GND fan-out vias and +5V tap vias before routing, Freerouting 2.5.0 with upstream tracks locked, then a grid finisher (`gen/finish_routes.py`) for what Freerouting leaves. Passives moved to 0402 where the rating allows (2026-10-23, to free bottom area; R6/R8/R9/C16/C17 stay 0603/1206). Analog-stage nets routed by negotiated routing (`finish_routes.negotiate`) before Freerouting. Routing closed 2026-10-23 (r32): `checks/drc_vs_upstream.py` = 0 new violations, 0 unconnected; the last open connection (D3 clamp to +5V) was fixed by `close_d3_link` in the generator, found with `checks/whatif_route.py`. **Not done (updated 2026-10-23 evening):** self-audit done, see `RELEASE_ASSESSMENT.md`; firmware fix R4 (CAN thread no longer waits 100 ms with no node on the bus); the C17 move was tried (r33, weighting `/VOP12`) and reverted (6 open). C17 sits 4.5 mm from U6 pin 8 (fix before review); silkscreen overlaps; audit (pack in `work/audit/carrier-d-2026-10-23/`, hand-off in `AUDIT.md`); BOM/CPL and JLC quote. Run history and next steps in `HANDOFF.md`. The board file in the repo is this WIP state; don't order from it (release.py would refuse anyway). For the audit: R8 (330R) and R9 (1k) are 0603 (100 mW); an AOUT short to GND or a load-dump surge into the zener exceeds that briefly or steadily (INFERRED, not simulated); consider 0805/1206 or a pulse-rated part. Open: how the owner will flash the module (SWD probe or rusEFI over CAN). Open: invalid-output value (owner), owner to confirm tests A1-A3.
- Baseline checks on upstream at its HEAD (2026-10-23, error level): module DRC 11 / ERC 0; carrier DRC 29 / ERC 8. Not yet judged as real or harmless.
