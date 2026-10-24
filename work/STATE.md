# STATE — rusEFI wideband (module + carrier)

Status: 2026-10-23 — Codex round 3 plus follow-up; board unchanged (r36, 40.0 x 51.5 mm). DRC delta 0 new / 0 open, no drift. Small-signal and four ramped full-scale model runs complete. Layout checker repaired and regression-tested; now flags PWM return component 6.8 mm. Suite: 8 pass / 3 fail (two inherited DRC checks plus PWM review). Open: fault back-feed/sink behavior, full-scale load/tolerance, receiver grounding, PWM return review. See AUDIT.md and docs/codex-audit-2026-10-23.md; historical confidence percentages are not evidence.
Revision in progress: none yet   Revisions used (never reused): none by the owner. Upstream module exports are rev A, B, C (upstream's own scheme, not ours).
<If the project already names revisions its own way (v1.0.0), keep its scheme.>
Review pages: status report https://claude.ai/artifact/YRsjXKGZKG5AFbwkcMuYZ4 (private; rebuilt by `checks/report.py`)  fit check <link>  audit <link>

## Stages
Mark a stage done only when its exit condition is true. Strike through, don't delete.

| # | Stage | Exit condition | Done |
| --- | --- | --- | --- |
| 1 | Requirements | `REQUIREMENTS.md` answered by the owner; breakout/perfboard ruled out | |
| 2 | Parts | Every part in `parts_research.md` with pinout, land pattern, temp rating, stock, source URL; real 3D model seen for user-handled and tall parts | |
| 3 | Schematic | Generated from code; netlist self-check passes | |
| 4 | Fit check | Artifact page with the to-scale picture and size table (mm + in) approved by the owner | |
| 5 | Placement | Fixed parts and critical loops locked; back side checked | |
| 6 | Routing | Best run chosen by DRC count, not router score; vias out of SMD pads | |
| 7 | 3D and mechanical | Access check done for every user-handled part; renders looked at, then published and approved by the owner | |
| 8 | Fab files | `checks/run_all.py` all PASS (DRC included, nothing skipped) on the current design | |
| 9 | Audit | `AUDIT.md` round with no open BLOCKER or BUG; earlier fixes re-confirmed | |
| 10 | Order | `checks/release.py` released `fab/<rev>/`; committed the same day; row in `ORDERS.md` | |
| 11 | Bring-up | Bring-up tests from `REQUIREMENTS.md` run and recorded below; RISK items checked; lessons in `LESSONS.md` | |

## Decisions already made (do not re-ask)
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
| DRC module (errors) | FAIL | DRC 11 errors: solder_mask_bridge 10, clearance 1 (report checks/out/wideband_controller-drc.json) | 2026-10-23 | `wideband_controller.kicad_pcb` 0179d031bc63 |
| ERC module (errors) | PASS | ERC 0 errors (report checks/out/wideband_controller-erc.json) | 2026-10-23 | `wideband_controller.kicad_sch` e54843a1e6ef |
| DRC carrier (errors) | FAIL | DRC 23 errors: courtyards_overlap 14, copper_edge_clearance 3, malformed_courtyard 3, starved_thermal 2 (report checks/out/board_carrier-drc.json) | 2026-10-23 | `board_carrier.kicad_pcb` 8db07cd11e6b |
| Carrier DRC vs upstream baseline (new violations, unconnected) | PASS | DRC vs upstream: 0 new violations, 0 unconnected | 2026-10-23 | `board_carrier.kicad_pcb` 8db07cd11e6b |
| Carrier: no new vias in SMD pads | PASS | via in pad: 0 new, 0 upstream | 2026-10-23 | `board_carrier.kicad_pcb` 8db07cd11e6b |
| Carrier layout review (sampled coupling and return-path heuristics) | FAIL | review triggers: 1 (return path /AOUT_PWM) | 2026-10-23 | `board_carrier.kicad_pcb` 8db07cd11e6b, `layout_review.py` 2dfa9e8efa14, `layout_metrics.py` 23c78d58fd8a |
| Layout geometry helper unit tests | PASS | OK | 2026-10-23 | `layout_metrics.py` 23c78d58fd8a, `test_layout_metrics.py` 2d93b205dd56 |
| Layout track-order regression | PASS | PASS: tested orders agree | 2026-10-23 | `board_carrier.kicad_pcb` 8db07cd11e6b, `layout_review.py` 2dfa9e8efa14, `layout_metrics.py` 23c78d58fd8a, `audit_layout_order.py` c40bda9f97e2 |
| ERC carrier (errors) | PASS | ERC 0 errors (report checks/out/board_carrier-erc.json) | 2026-10-23 | `board_carrier.kicad_sch` c2190cd03e68 |
| Carrier netlist self-check (generator table) | PASS | netlist self-check: 18 nets, 0 problems | 2026-10-23 | `board_carrier.kicad_sch` c2190cd03e68, `gen_carrier_sch.py` ae5a44d3abf4 |
| No hand edits waiting | PASS | no drift | 2026-10-23 |  |

Written by `checks/run_all.py` at commit 34cd49d. Don't edit by hand.
<!-- checks:end -->

## Bring-up results
| Test | Board # | Reading | Pass? | Date |
| --- | --- | --- | --- | --- |

## Firmware tested on
| Board revision | Firmware commit | Result |
| --- | --- | --- |

## Open
- 2026-10-23 Codex follow-up: layout metric repaired and regression-tested; PWM return review flag is 6.8 mm (C7). Four ramped full-scale model runs succeeded: about 5.019 V into 100k, 4.816 V into 10k, at protected supplies 12 V and 7.5 V. C1/C2/C3 remain open. Default: retain components until load/tolerance and clamp/sink behavior are jointly budgeted. 80R instead of 470R is not a standalone accuracy fix. See audit report follow-up. Long paragraph below is historical context, not current layout status.
- Analog output: `docs/analog-out.md`, `docs/carrier.md`, `docs/firmware.md`, `sim/analog_out.cir`. Firmware on branch `analog-out` builds (2026-10-23): PB1/TIM3_CH4, updated from the CAN TX thread, compiled-in 10-20 AFR curve, 0 V while invalid, full scale 5.04 V; 4.8 KB flash, 8 B RAM left; untested on hardware. Carrier analog stage proposed with parts (REF3030 C38423, 74LVC1G125 C12519, LM2904DR C7934, BAT54S C47546) and a behavioral filter simulation (0.7 mV ripple, 4.1 ms settling). Op-amp stability checked with TI's LM2904 model: feedback after the 330R oscillates; dual loop with Cf 1 nF has no overshoot from 1 pF to 47 nF (`sim/stability.sh`). Firmware test mode (SEL_2 low at power-up) and compiled-in trim added; RAM now full to the byte (no runtime allocation, so safe). Carrier schematic generated from code (`gen/gen_carrier_sch.py`, A3 sheet, upstream drawing kept): ERC 0 errors, netlist self-check 17/17 nets (2026-10-23). Carrier PCB in progress (`gen/gen_carrier_pcb.py`, 2026-10-23): new parts on the bottom (board can't grow inside `case/case.STL`; case clearance under the board about 6 mm, INFERRED); placed by an annealing placer (net length + distance to existing copper), GND fan-out vias and +5V tap vias before routing, Freerouting 2.5.0 with upstream tracks locked, then a grid finisher (`gen/finish_routes.py`) for what Freerouting leaves. Passives moved to 0402 where the rating allows (2026-10-23, to free bottom area; R6/R8/R9/C16/C17 stay 0603/1206). Analog-stage nets routed by negotiated routing (`finish_routes.negotiate`) before Freerouting. Routing closed 2026-10-23 (r32): `checks/drc_vs_upstream.py` = 0 new violations, 0 unconnected; the last open connection (D3 clamp to +5V) was fixed by `close_d3_link` in the generator, found with `checks/whatif_route.py`. **Not done (updated 2026-10-23 evening):** self-audit done, see `RELEASE_ASSESSMENT.md`; firmware fix R4 (CAN thread no longer waits 100 ms with no node on the bus); the C17 move was tried (r33, weighting `/VOP12`) and reverted (6 open). C17 sits 4.5 mm from U6 pin 8 (fix before review); silkscreen overlaps; audit (pack in `work/audit/carrier-d-2026-10-23/`, hand-off in `AUDIT.md`); BOM/CPL and JLC quote. Run history and next steps in `HANDOFF.md`. The board file in the repo is this WIP state; don't order from it (release.py would refuse anyway). For the audit: R8 (330R) and R9 (1k) are 0603 (100 mW); an AOUT short to GND or a load-dump surge into the zener exceeds that briefly or steadily (INFERRED, not simulated); consider 0805/1206 or a pulse-rated part. Open: how the owner will flash the module (SWD probe or rusEFI over CAN). Open: invalid-output value (owner), owner to confirm tests A1-A3.
- Baseline checks on upstream at its HEAD (2026-10-23, error level): module DRC 11 / ERC 0; carrier DRC 29 / ERC 8. Not yet judged as real or harmless.
