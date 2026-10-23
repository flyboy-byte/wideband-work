# STATE — rusEFI wideband (module + carrier)

Status: Scaffolded, stage 1 Requirements not started (2026-10-23)
Revision in progress: none yet   Revisions used (never reused): none by the owner. Upstream module exports are rev A, B, C (upstream's own scheme, not ours).
<If the project already names revisions its own way (v1.0.0), keep its scheme.>
Review pages: fit check <link>  renders <link>  audit <link>

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
- 2026-10-23 Work in a separate repo (`wideband-work`), upstream clone `../wideband` stays untouched — owner's choice.
- 2026-10-23 Upstream's `hardware/*/export/` files are upstream releases, not evidence of anything the owner ordered.

## Checks
<!-- checks:start -->
| Check | Result | Summary | Date | Files (sha256/12) |
| --- | --- | --- | --- | --- |
| DRC module (errors) | FAIL | DRC 11 errors: solder_mask_bridge 10, clearance 1 (report checks/out/drc.json) | 2026-10-23 | `wideband_controller.kicad_pcb` 0179d031bc63 |
| ERC module (errors) | PASS | ERC 0 errors (report checks/out/erc.json) | 2026-10-23 | `wideband_controller.kicad_sch` e54843a1e6ef |
| DRC carrier (errors) | FAIL | DRC 29 errors: courtyards_overlap 14, clearance 8, malformed_courtyard 3, starved_thermal 2 (report checks/out/drc.json) | 2026-10-23 | `board_carrier.kicad_pcb` 71d343b660c5 |
| ERC carrier (errors) | FAIL | ERC 8 errors: pin_not_driven 3, power_pin_not_driven 3, pin_not_connected 2 (report checks/out/erc.json) | 2026-10-23 | `board_carrier.kicad_sch` 1c4a6695af9a |

Written by `checks/run_all.py` at commit no-git. Don't edit by hand.
<!-- checks:end -->

## Bring-up results
| Test | Board # | Reading | Pass? | Date |
| --- | --- | --- | --- | --- |

## Firmware tested on
| Board revision | Firmware commit | Result |
| --- | --- | --- |

## Open
- What does the owner want to do with this board: build and order as is, adapt it, or learn from it? (owner)
- Baseline checks on upstream at its HEAD (2026-10-23, error level): module DRC 11 / ERC 0; carrier DRC 29 / ERC 8. Not yet judged as real or harmless.
