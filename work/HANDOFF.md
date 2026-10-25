# HANDOFF — dense session context (read after STATE.md)

Written 2026-10-25 (Opus 5.5) at the end of the session that answered round 6. Replaces the 2026-10-24 version (in git
history). Replace it at the next handoff.

## Verify first, don't assume
- `git status`: clean except `hardware/board_carrier/~board_carrier.kicad_pro.lck`, a stale KiCad lock from 2026-10-23
  (KiCad isn't running; leave it). `git branch --show-current` must say `analog-out`: **Codex once ran in this checkout
  and left it on its review branch**, so later edits landed there. `git log --oneline -5`. `master` = upstream
  mck1117/wideband; `upstream` push disabled; `origin` = public fork. Push is allowed (owner lifted the hold 2026-10-24).
- `cd work && python3 checks/run_all.py`: **26 checks, 0 failed, 2 advisory** (raw upstream DRC, owner decision D2).
  A reviewer runs `python3 checks/run_all.py --report DIR` instead (leaves STATE.md and tracked reports alone).
- Firmware: `cd firmware/boards/f0_module/bootloader && ./build_bootloader.sh`, then `make -C firmware -j8 BOARD=f0_module`
  (the stack check reads `firmware/build/wideband.elf`; rebuild f0 last). Host tests 70/70 (`checks/host_tests.py`),
  aux 21/21 (`make -C test/aux_out run`).
- Sims (TI model in `sim/models/`, not committed): one at a time under `nice`; on this shared machine stability takes
  tens of minutes each (full scale took about an hour on 2026-10-25).

Last raw output (2026-10-25, after the round 6 fixes):
```
FAIL  DRC module (errors): DRC 11 errors: solder_mask_bridge 10, clearance 1  [advisory, D2]
FAIL  DRC carrier (errors): DRC 23 errors: courtyards_overlap 14, copper_edge_clearance 3, ...  [advisory, D2]
PASS  Carrier DRC vs upstream baseline: 0 new violations, 0 unconnected
PASS  JLC rotation (carrier): 38 parts measured, 4 need a correction, 0 problem(s)
PASS  Fab candidate matches the board: 38 placed, 6 not fitted, outline 40.00 x 51.50 mm, 0 problem(s)
PASS  Host gtest suite: [  PASSED  ] 70 tests.     PASS  Analog output host tests: [  PASSED  ] 21 tests.
PASS  Static worst-case stack: ok, smallest margin 92 B     PASS  Stack checker cases: 4, 0 wrong verdict(s)
PASS  Sim wrappers: 0 wrong verdict(s)     PASS  Boot level: output low from reset
PASS  Module order files: 57 parts measured, 6 need a correction, 0 problem(s)
PASS  Reviewer docs agree with the repo: 0 problem(s)     PASS  Surge budget: 0 problem(s)
26 checks, 0 failed, 2 advisory failed, 0 skipped   (the other 12 pass as before: last_run.json)
```

## Where things stand (2026-10-25)
- **Board**: r41 layout, unchanged since 2026-10-24. Part changes: R3 4.7k (B1, 2026-10-24), **R9 C844867** (Vishay
  CRCW1206 HP pulse-proof, 0.75 W; R6-S3, 2026-10-25), one LCSC field each in the board and schematic. Fab candidate
  `work/out/carrier/` re-exported (26 BOM lines, 8 Extended). Not released; nothing ordered.
- **Firmware**: unchanged in behaviour since 2026-10-24 (PB1 pull-down, invalid = 5.0 V, heater clamp, watchdog);
  2026-10-25 changed two comments only.
- **Audits**: rounds 1-6 recorded in `AUDIT.md`. Round 6 (Codex/Astra, PR #2, merged by fast-forward): 2 BUG
  (both in our checkers: stack checker, sim wrappers), 3 RISK, 3 NOTE; 5 fixed, 2 accepted, each fix with a
  regression that fails on the old code. **Round 7 running now** (owner started Astra on 2026-10-25 with the prompt
  below; its folder will be `work/audit/astra-2026-10-25b/`, branch `review/astra-2026-10-25b`, in its own worktree
  `../wideband-review-astra`). Tasks: `review/TASKS.md` TK1-TK7.
- **Cousin (sidewinderzz)**: no activity since his round 5 branch (2026-10-24 21:43 UTC); his `analog-out` is behind.
- **Module**: `gen/module_fab.py` stages upstream rev C (R10/C3 substituted, J1/J3 off BOM, Q1 CPL 180 -> 0). U9
  pinout settled by round 6 from Torex's datasheet.
- **Recommendation given to the owner (2026-10-25)**: after round 7, if there's no BLOCKER or BUG, release and order;
  stop routine desk reviews; the next review worth paying for comes after bench data (A1-A8).

## Next, in order
1. **Round 7 result**: when the owner says it's done, check `gh pr list -R flyboy-byte/wideband-work`, read
   `work/audit/astra-2026-10-25b/FINDINGS.md`, verify each finding yourself (fix + regression that fails on the old
   code, or a written answer), add a "Round 7" section to `AUDIT.md`, merge the PR (it should only add its folder:
   check `git diff --name-only analog-out...origin/<branch>`).
2. **Release** (if no open BLOCKER/BUG): `python3 gen/export_fab.py`, `python3 checks/run_all.py`, then
   `python3 checks/release.py <new rev> out/carrier/carrier-gerbers.zip out/carrier/carrier-bom.csv out/carrier/carrier-cpl.csv out/carrier/not-fitted.csv`.
   `release.py` needs the last audit round to cover the current design. Revision letters used: `STATE.md`.
3. **Order** (owner, money): `docs/ordering.md`. Edge rails for C11 (R6-S4); placement preview Q1 (module) and D2
   (carrier) first; `checks/bom_stock.py 5` on the day. About $180-215 for 5 + 5 (`ROADMAP.md`).
4. **Owner purchases**: HiLetgo ST-Link V2 + TC2030-IDC-NL + jumpers, LSU 4.9 + Bosch 1 928 404 669 plug kit,
   Molex 36792-1201 (terminals and seals from AS-36783-001-001). Bench tests: `docs/carrier.md` A1-A8, W1, H1-H6.

Round 7 start (the owner pasted this into Codex):
```
cd ~/projects/wideband-work && git pull && codex
Independent review, round 7. Check our round 6 fixes; don't trust our docs. Read REVIEW.md, then work/review/TASKS.md,
then the "Hand-off" in work/AUDIT.md. Work in your own worktree (git worktree add ../wideband-review-astra -b
review/astra-2026-10-25b), folder work/audit/astra-2026-10-25b/, with FINDINGS.md copied from
work/review/FINDINGS-TEMPLATE.md. Work TK1-TK7 in order without waiting for me; update FINDINGS.md and commit after each
task. Run checks with `python3 checks/run_all.py --report <your folder>`. Don't change design files. With a quarter of
your budget left, write the verdict, push, and open a PR to flyboy-byte/wideband-work.
```

## This session (2026-10-25), what changed and where
| Item | What | Evidence |
| --- | --- | --- |
| Review docs | `REVIEW.md` (three rules, two routes, agent prompt with worktree), `review/TASKS.md`, `review/FINDINGS-TEMPLATE.md`, `review/PROMPT.md`; pack adds plain-text part/net lists (`checks/pack_extras.py`), module Gerbers, `INDEX.md`, a zip | `checks/review_docs.py` (self-test 5/5) |
| Pack bug | carrier and module `README.md`/`not-fitted.csv` collided; module's overwrote the carrier's | `audit_pack.py` refuses collisions, `FILE=NAME` renames |
| R6-S6 | stack checker cut real recursion through pointers | `NARROW` table + every loop fails; test case 4 fails (hangs) on the old checker; production margin 92 B |
| R6-S8 | aborted ngspice runs passed all three wrappers | `sim/completed.sh`; 9 fake cases fail on the old wrappers; real runs 25/25, 48/48, 27/27 (full scale identical) |
| R6-S7 | stability step before the output settled | step at 3 ms + 0.5 mV drift guard; `sim/stability.out`: E 0 % to 10 nF, 9.2 % / 22.4 % at 47 / 100 nF |
| R6-S3 | R9 250 mW at 0.475 W in a clamped load dump | R9 -> C844867; `checks/surge_budget.py` fails on C4410 |
| Docs | offset budget 7 mV max (R6-S1); fuse wording (R6-S5); 35-48 V -> 27-39 V; bench test A8 (backfeed); edge rails step; `run_all.py --report` | `AUDIT.md` round 6 |
| Skill | `pcb-design` updated and pushed (dotfiles): reviewer briefing, `templates/review/`, scripts (`run_all --report`, advisory, `audit_pack` fixes), sim completion, surge budget | `~/.claude/skills/pcb-design` and `~/.agents/skills/pcb-design` in step |

## Board run history (generator `gen/gen_carrier_pcb.py`, seed 7)
| Run | Change | Result |
| --- | --- | --- |
| r41 | copper keep-out r 3.6 mm around H1/H2, both layers (`HOLE_KEEPOUT`, permanent rule areas): r37-r40 had GND pour 0.3 mm from the holes and a +5V track 3.0 mm from H1 centre, under a screw head and washer. A3 expectation corrected (about 6 mA) | placement identical; 0 new / 0 open / 0 via-in-pad / layout 0 triggers; nearest copper 4.1 mm (H1), 5.4 mm (H2); fab candidate re-exported; 20 checks 0 failed (current) |
| r40 | silkscreen stroke 0.16 mm (skill minimum); fab export `gen/export_fab.py` -> `work/out/carrier/` (gitignored); `checks/jlc_rotation.py` and `checks/fab_files.py` | placement identical; 0 new (strict) / 0 open; JLC: 38 parts, corrections U1/U6 270, U4/U5 180, U2 shifted 0.725 mm; D2 paired by pin name (EasyEDA numbers the SS54 anode 1); run_all 20 checks 0 failed |
| r39 | silkscreen pass (`gen/silk.py`): 1.0/0.15 mm labels (JLC minimum), jumper function labels TEST and 120R, a label only where it reads as its own part (0.4 mm margin), else hidden | placement identical; 11 labels shown, 13 passives hidden; 0 silk issues on new parts except upstream's relabelled bottom "TEST" clipping a pad; 0 new (strict) / 0 open / 0 via-in-pad / layout 0 triggers. The via merge kept the router's via this time (order not fixed; DRC confirms connectivity) |
| r38 | `merge_close_vias()` after routing; `drc_vs_upstream.py` now also counts fab-relevant warnings (FAB_WARNINGS) | placement identical to r37; one router +5V via merged into the tap via; 0 new (strict) / 0 open / 0 via-in-pad / layout 0 triggers |
| r37 | parts to the TOP (SIDE, D9), R6 feedback from J3-5 after R11 (C2), R9 1206 (D1), M3 holes H1/H2 (D8) | 0 new / 0 open / 0 via-in-pad; layout review 0 triggers (PWM return 4.1 mm, was 6.8: C7 cleared); C17 2.7, C15 2.3, C12 2.1, C11 3.9 mm (feed reaches C11 first); bottom carries only tracks; renders `renders/carrier-f/`; **had two +5V vias 0.225 mm apart (hole_to_hole warning), as r26-r36 had a GND or +5V pair: found 2026-10-24, fixed r38** |
| r36 | C17/C15 start targets on the mirrored-correct side, bypass weight 8 | 0 new / 0 open / 0 via-in-pad; C17 2.1 mm, C15 2.3 mm |
| r35 | CAN terminator to the strip's left end; output under the corridor right of the cutout | coupling clean; C17 6.1 mm |
| r34 | board +15 mm, stage in the strip, R11, upstream tracks kept (`REROUTE = []`) | 0/0 first try; CAN_L 0.3 mm beside output 6.8 mm |
| r33 | `/VOP12` weight on the small board | 6 open: reverted |
| r32 | `close_d3_link` (found with `checks/whatif_route.py`) on the small board | 0/0; superseded, now dead code (prints "skipped") |
| r17-r31 | pre-routing orders, PathFinder negotiation, seed sweeps, island joins, vias out of pads | details in git history of this file |

## Design facts a cold session would otherwise re-derive
- Analog out: module pad SEL_1 = PB1 = TIM3_CH4 (AF1), shares the pump-DAC timer (48 MHz / 1024 = 46.9 kHz). Curve
  10 AFR = 0 V ... 20 AFR = 5 V; **invalid lambda -> 5.0 V** (lean end, since 2026-10-24); test mode when SEL_2 is low at
  power-up (also moves the CAN ID offset to 4). Updated from the CAN TX thread; CAN frames dropped, not waited for.
- Stage: R3 4.7k pull-down (+ PB1 pull-down in both board.h) -> 74LVC1G125 on REF3030 3.000 V -> 2x 3.3k/100n ->
  LM2904 x1.68 dual loop (DC from J3-5 after R11, 1 nF from the op-amp output) -> 330R -> 1N4148WS clamps to +5V/GND ->
  R11 470R -> J3-5. LM2904 supply `/LSU_Heater+` -> R9 1k (C844867) -> `/VOP12`, 18 V zener D5. Plain LM2904 is 26 V
  rated, offset 7 mV max.
- J3-5 sits between J3-6 (12V_RAW) and J3-4 (LSU_Heater+). J3-1 and J3-7 are the same GND net.
- f0 system time: 16 bits at 10 kHz (wraps 6.55 s); use `chVTGetTimeStamp()` for anything longer. IWDG watchdog
  refreshed by the heater loop (`firmware/watchdog.h`).
- Stack checker: the only `ISampler` is `Sampler`, the only `IHeaterController` is `HeaterController`; five callers
  narrowed in `checks/stack_estimate.py` `NARROW`. A new virtual class or callback makes it fail until the table is
  updated: that's intended.

## Tool quirks
- `pkill -f` / `pgrep -f NAME` match your own shell (exit 144): kill by PID. A background "completed" notice can be the
  launcher, not the job: grep its log for a DONE marker.
- Make doesn't rebuild on flag changes (UDEFS): `touch` the file. Quoted includes search the including file's directory
  before `-I` (matters for host shims). clangd errors in this tree are noise; the real builds decide.
- pcbnew (KiCad 10): `board.BuildConnectivity()` before `GetConnectedItems(item)`; `board.FindNet(name)`;
  `pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)`. Bottom-side footprints are mirrored: pin 8 of a rot-0 SOIC is
  lower right. The placer's half-perimeter cost ignores where a cap sits inside its net: use `BYPASS` pairs.
- QEMU 11.1 `-M microbit` is a Cortex-M0 for instruction-level tests; it is not this chip (QEMU has no F042).
- `drift.py record` keeps a snapshot under `work/checks/hardware/` (tracked, commit it with the board).
- ngspice exits 0 after aborting a transient and prints zeros for windows it never reached: wrappers check `END`
  against the stop time (`sim/completed.sh`).
- bash reads a script as it runs: don't edit a `sim/*.sh` while it's running.
- A Codex reviewer in the same checkout switches its branch: reviewers use `git worktree` (REVIEW.md).

## Owner (Logan)
Autonomy on "keep going": reversible steps, questions + defaults into STATE.md; stop for money, deleting, overwriting his
KiCad edits, publishing. Pushing is fine now. Function first on this prototype (no enclosure/fit gates; he does the case
in CAD last). Hands-on tuner; learning project; bench = multimeter + iron; reviews from his phone; JLC places SMD, he
solders through-hole. "Astra" = Codex (GPT models) on this machine, logged into his GitHub. Don't send lessons back to
the cousin's skill (owner, 2026-10-24).

## Do not re-raise
Buying a ready-made controller; forking lambda-x2 / wideband-F103; narrowband simulation output; the Honda side; CAN-ID strap
trade-off; separate repos; negotiating the whole +5V branch; upstream's case.STL as a size limit; upstream's own analog
output (PR #352); engine-bay heat as a design driver.
