# HANDOFF — dense session context (read after STATE.md)

Written 2026-10-23, updated through 2026-10-24 (Opus 5.5: r37-r41, watchdog, fab export, open register). Replace at the next handoff.

## Verify first, don't assume
- `git status` (clean except `hardware/board_carrier/~board_carrier.kicad_pro.lck`: KiCad's lock, maybe the owner has it
  open, leave it), `git log --oneline -12` (branch `analog-out`). `master` == upstream mck1117/wideband 2bb80d2; `upstream`
  push disabled; `origin` = public fork, push only when the owner says.
- `cd work && python3 checks/run_all.py`: 16 checks, 3 known fails (raw output below).
- Firmware: the in-tree f0 build links the bootloader object, so after any bootloader `make clean` run
  `cd firmware/boards/f0_module/bootloader && bash build_bootloader.sh` first; then `cd firmware && make -j12 BOARD=f0_module`.
  `make clean` when switching BOARD (stale objects fail the f1_dual link with `EFLD1` undefined). Staged, reproducible
  package instead: `python3 work/checks/fw_package.py build` -> `work/fw-build/<commit>/` (gitignored).
- Host tests: `B=$(mktemp -d) && mkdir -p $B/obj $B/lst && (cd test && make -j8 BUILDDIR=$B) && $B/wideband_test` -> 69/69 (or `python3 work/checks/host_tests.py`, also in run_all)
  (absolute BUILDDIR: no more moving `firmware/build` aside). `make -C test/aux_out run` -> 21/21.
- `checks/stack_estimate.py` reads `firmware/build/wideband.elf` and fails on a non-f0 build: rebuild f0 last.

Last raw output (2026-10-24, board r41, after commit a6fa711):
```
FAIL    DRC module (errors): DRC 11 errors: solder_mask_bridge 10, clearance 1 (report checks/out/wideband_controller-drc.json)  [advisory]
PASS    Module board identical to upstream: module board vs upstream master: 0 file(s) differ
PASS    ERC module (errors): ERC 0 errors (report checks/out/wideband_controller-erc.json)
FAIL    DRC carrier (errors): DRC 23 errors: courtyards_overlap 14, copper_edge_clearance 3, malformed_courtyard 3, starved_thermal 2 (report checks/out/board_carrier-drc.json)  [advisory]
PASS    Carrier DRC vs upstream baseline (new violations, unconnected): DRC vs upstream: 0 new violations, 0 unconnected
PASS    Carrier: no new vias in SMD pads: via in pad: 0 new, 0 upstream
PASS    Carrier layout review (sampled coupling and return-path heuristics): review triggers: 0
PASS    Layout geometry helper unit tests: OK
PASS    Layout track-order regression: PASS: tested orders agree
PASS    ERC carrier (errors): ERC 0 errors (report checks/out/board_carrier-erc.json)
PASS    Carrier netlist self-check (generator table): netlist self-check: 18 nets, 0 problems
PASS    No hand edits waiting: no drift
PASS    JLC rotation, origin and pin names from each part's EasyEDA footprint: jlc rotation: 38 parts measured, 4 need a correction, 0 problem(s)
PASS    Fab candidate (out/carrier) matches the board: Gerbers, BOM, CPL, not-fitted: fab files: 38 placed, 6 not fitted, outline 40.00 x 51.50 mm, 0 problem(s)
PASS    Firmware: bootloader DATA writes stay inside the app partition (F1): 52 guard cases; 0 unsafe accepted writes, 0 valid writes refused (stub only)
PASS    Firmware: package checker accepts good images, rejects bad ones (F2): 21 package cases, 0 wrong verdict(s)
PASS    Firmware: HardFault entry reaches the C handler on a Cortex-M0 (F9, QEMU microbit): fault entry on Cortex-M0: as expected
PASS    Firmware: host gtest suite (sampler, heater, F7, F1 bounds, D10 watchdog): [  PASSED  ] 69 tests.
PASS    Firmware: analog output host tests, production auxout/pump_dac/can_helper on the f0 config (F3-F6): [  PASSED  ] 21 tests.
PASS    Firmware: static worst-case stack per thread fits (F8 estimate, f0 build): stack estimate: ok, smallest margin 80 B
20 checks, 0 failed, 2 advisory failed, 0 skipped
```

## Where things stand (2026-10-24, late; supersedes the block below)
- **Board**: r41 layout + B1 fix (R3 4.7k C25900) + J3 bottom labels (OUT, GND, 12V restored). No parts moved since r41.
  24 checks: 0 failed, 2 advisory (raw upstream DRC, D2). Pushed: `analog-out` on origin.
- **Firmware**: PB1 pull-down (app + bootloader), invalid = 5.0 V, heater voltage clamped at 0 (upstream bug), watchdog.
  Host 70 + aux 21 tests pass; stack margin 64 B. Flash package `work/fw-build/ba01449/` checked (gitignored; rebuild
  with `checks/fw_package.py build`).
- **Audits**: rounds 4 (Codex, fork PR #1 merged) and 5 (cousin's Claude, branch on `sidewinderzz/wideband-work`,
  cherry-picked) answered in `AUDIT.md`. **Round 6 open**: hand-off in `AUDIT.md` (8 items), `REVIEW.md`, pack
  `sh checks/review_pack.sh`. Watch for a PR from the cousin.
- **Module**: `gen/module_fab.py` stages upstream rev C with R10/C3 substituted, J1/J3 off the BOM, Q1 CPL corrected
  (180 -> 0, would have gone on turned); `checks/jlc_rotation.py --board module` 57/57.
- **SWD (D4, owner)**: HiLetgo ST-Link V2 clone + TC2030-IDC-NL + jumpers; table and `st-flash` command in `docs/wiring.md`.
- **Route, costs, shopping list, manufacturer**: `ROADMAP.md`. Wiring: `docs/wiring.md`. Ordering: `docs/ordering.md`.
- **Open**: round 6; Torex XC6206 pin table (site blocks fetches; owner can read it in a browser); TC2030 plug fit
  through the cutout (try with the cable); J3 terminals/seals for Molex 36792-1201; owner's purchases and the order.
- Tool quirks found today: `LESSONS.md` (bc and exponents, pkill matching itself, EasyEDA needs curl, TI model can't
  solve its operating point through R9: use `uic`).

## Where things stand (2026-10-24)
- **External review ready** (later 2026-10-24): `REVIEW.md` at the root (fresh-clone setup, blind pack via
  `sh checks/review_pack.sh` or full repo, report format, where raw output goes); verified by a scratch clone running
  all 20 checks. Pushed 2026-10-24 (analog-out 8ad4b28, dotfiles 70aa5e9).
- **Board r41**: 40.0 x 51.5 mm; analog stage on the TOP (one-sided JLC Economic assembly); DC feedback from J3-5 after
  R11 (load-independent, `sim/load_accuracy.sh`, `sim/stability.sh` topology E); R9 1206; M3 holes H1/H2 with 3.6 mm
  copper keep-out; overlapping-via merge; silkscreen pass (TEST/120R jumper labels). Renders `renders/carrier-f/`
  (top, bottom, assembly-top.svg). Status page v3: https://claude.ai/artifact/YRsjXKGZKG5AFbwkcMuYZ4
- **Fab candidate** `work/out/carrier/` (gitignored, rebuild with `python3 gen/export_fab.py`): BOM 25 lines (7 Extended),
  CPL 38 parts with EasyEDA-measured rotations (`checks/jlc_rotation.py`; D2 paired by pin name, U2 shifted 0.725 mm),
  checked by `checks/fab_files.py`. Not released; nothing ordered.
- **Firmware**: F1-F9 done; D10 watchdog done (`firmware/watchdog.h`, bench self-test `WB_WATCHDOG_SELFTEST`). Host 69 + aux 21.
- **Audit**: round 4 pending (Codex). Pack `audit/carrier-f-2026-10-24/` was built at r40: rebuild at r41 first.
- **Everything open**: `STATE.md` "Open register" (board/fab, module board not prepared, firmware, deeper tests, bench).
- **Skill**: `~/.claude/skills/claude-usage/` (bridge key `~/.config/libre-bridge/keys/claude-usage.key`, read:usage only).

## This session's firmware work (Opus, after Codex), in order
| Item | What | Evidence | Commit |
| --- | --- | --- | --- |
| F1 | Bootloader CAN DATA writes bounded to the 25 KiB app partition (was 26 KiB, offset+length unchecked) via `bootloader_bounds.h`, size from linker symbol `__appflash_size__` | harness 52 cases 0 unsafe + 4 must-accept; old bound as mutant fails; 8 gtest | f2a437c |
| F2 | `fw_package.py build/check`: upstream's format staged without `build_wideband.sh`'s deletes; CRC via the bootloader's own `isAppValid()` compiled on host + zlib; M0 vector tables | upstream's shipped image passes, header reproduced byte-for-byte; 21 good/bad cases; two builds identical | 783a885 |
| F9 | HardFault entry was Thumb-2 (`.cpu cortex-m3`): on the M0 a fault locked up, never reset; `bkpt()` in handlers did too | QEMU microbit Cortex-M0: old entry and BKPT lock up, new entry reaches C handler; f0 build 0 Thumb-2 ops | 8e9fa1c |
| F3-F5 | `test/aux_out/`: production auxout/pump_dac/can_helper on the real f0 config + fake ChibiOS | 16 tests; **found F5: test mode stuck at 1.00 V** (16-bit systime wraps 6.55 s); fixed with 64-bit `chVTGetTimeStamp()`; old code fails exactly at 2.50/4.00 V points | 1c8f942 |
| F6 | the production CAN TX loop run for N windows in `test/aux_out` (fake `chThdSleepUntilWindowed` throws to stop it) | 5 tests: one update per 10 ms cycle with and without bus ACK, across the tick wrap, test mode end to end; blocking-send mutant fails 3, no-update mutant fails 5 | this commit |
| F8 | `stack_estimate.py`: static worst case per thread from the ELF | all fit, smallest margin 80 B (pump), CAN TX 312/512 | 5f966bf |
| D10 | IWDG watchdog refreshed by the heater loop (`firmware/watchdog.h`), 0 B RAM, +44 B flash, debug-freeze, bench self-test flag `WB_WATCHDOG_SELFTEST` | disassembly; 5 host tests; 3 mutants caught; f1_dual builds | 2026-10-24 |
| F7 | `test/tests/test_heater_update.cpp`: whole `Update()` path | 13 tests; 2 mutants caught; host 64/64 | 2c5e445 |

Also: curve moved to `boards/f0_module/aux_curve.h`; `AUXOUT_TRIM_GAIN/OFFSET` overridable per build with a static_assert
(0.8-1.2, +-0.5 V); app flash 21,488 B used, 4,108 B free; RAM unchanged (0 B free).

## Next, in order (updated 2026-10-24)
1. **Audit round 4** on the fab candidate: pack `audit/carrier-f-2026-10-24/` (PROMPT.md first). Owner runs Codex or
   another model on it; bring findings back as a round in `AUDIT.md`. `release.py` needs that round, naming the commit,
   with no open BLOCKER or BUG.
2. **JLC quote** (owner, money): upload `work/out/carrier/` (rebuild with `python3 gen/export_fab.py` first). In the
   placement preview look at every IC and diode, D2 above all (EasyEDA numbers its anode 1); the rotation sense is
   INFERRED. Check stock on C13585, C14663, C15849, C7934 (`parts_research.md`), and look for a Basic 470R 1206 for R11.
3. Then `checks/release.py <rev> work/out/carrier/*` (the owner picks the revision letter), commit `fab/<rev>/` the day
   the order is placed, row in `ORDERS.md`.
4. Open but not blocking: republish the status page (`report/tests.json` still lists r33-r36); bench test W1 (watchdog)
   and A1-A4 once hardware exists; the hidden labels are on `renders/carrier-f/assembly-top.svg`.

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
  10 AFR = 0 V ... 20 AFR = 5 V; invalid lambda -> 0 V; test mode when SEL_2 is low at power-up (also moves the CAN ID
  offset to 4). Updated from the CAN TX thread (no RAM for a thread); CAN frames dropped, not waited for (`can_helper.cpp`).
- Stage: 100k pull-down -> 74LVC1G125 on REF3030 3.000 V -> 2x 3.3k/100n -> LM2904 x1.68 dual-loop (DC after 330R + 1 nF) ->
  330R -> 1N4148WS clamps to +5V/GND -> R11 470R -> J3-5. LM2904 supply LSU_Heater+ -> 1k -> 18 V zener. Plain LM2904 is
  26 V rated, not 32 (Codex C6).
- J3-5 sits between J3-6 (12V_RAW) and J3-4 (LSU_Heater+). J3-1 and J3-7 are the same GND net.
- f0 system time: 16 bits at 10 kHz (wraps 6.55 s); use `chVTGetTimeStamp()` for anything longer. No watchdog on f0.
- Without CAN the f0 sampler reports 0 V supply for 5 s, then 13 V (not measured); heater ramps at about 10.5 s.
  Module has VBatt_Sense -> 100k/10k -> PB0, unused by the firmware.

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

## Owner (Logan)
Autonomy on "keep going": reversible steps, questions + defaults into STATE.md; stop for money, deleting, overwriting his
KiCad edits, publishing, pushing. Function first on this prototype (no enclosure/fit gates; he does the case in CAD last).
No assumed engineering decisions (AGENTS.md rules 7-8). Hands-on tuner; learning project; bench = multimeter + iron;
reviews from his phone; JLC places SMD, he solders through-hole.

## Do not re-raise
Buying a ready-made controller; forking lambda-x2 / wideband-F103; narrowband simulation output; the Honda side; CAN-ID strap
trade-off; separate repos; negotiating the whole +5V branch; upstream's case.STL as a size limit.
