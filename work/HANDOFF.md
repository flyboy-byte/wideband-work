# HANDOFF — dense session context (read after STATE.md)

Written 2026-10-23, end of a long day: Sonnet 5.5 (routing r32, self-audit), then Opus 5.5 (review, board growth r34-r36),
then Codex (independent audit, commits 4e4b5a5 and f3cf90c), then Opus 5.5 again (Codex's firmware plan F1-F9). This file
replaces all earlier handoffs; they are in its git history (`git log -p -- work/HANDOFF.md`). Replace it at the next handoff.

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

Last raw output (2026-10-23, HEAD 357755f):
```
FAIL    DRC module (errors): DRC 11 errors: solder_mask_bridge 10, clearance 1
FAIL    DRC carrier (errors): DRC 23 errors: courtyards_overlap 14, copper_edge_clearance 3, malformed_courtyard 3, starved_thermal 2
PASS    Carrier DRC vs upstream baseline: 0 new violations, 0 unconnected
PASS    Carrier: no new vias in SMD pads: 0 new, 0 upstream
FAIL    Carrier layout review: review triggers: 1 (return path /AOUT_PWM)          <- Codex C7, open, board unchanged
PASS    Layout geometry helper unit tests / track-order regression / ERC carrier 0 / self-check 18 nets / no drift
PASS    F1 bootloader bounds: 52 guard cases; 0 unsafe accepted writes, 0 valid writes refused
PASS    F2 package checker: 21 package cases, 0 wrong verdict(s)
PASS    F9 HardFault entry on Cortex-M0 (QEMU microbit): as expected
PASS    F3-F6 analog output host tests: 16 tests
PASS    F8 stack estimate: ok, smallest margin 80 B
16 checks, 3 failed, 0 skipped
```

## Where things stand
- **Board** (r36, commit 986c803): 40.0 x 51.5 mm (1.57 x 2.03 in), upstream's outline grown 15 mm at the bottom; analog
  stage in the new strip on the bottom; R11 470R 1206 (C4502) between the clamps and J3-5; routed clean first try.
  Unchanged since. Renders `work/renders/carrier-e/`; status page https://claude.ai/artifact/YRsjXKGZKG5AFbwkcMuYZ4 (private,
  shows r36; does not yet show the firmware work).
- **Audit**: rounds 1 (Sonnet self), 2 (Opus review), 3 (Codex) in `AUDIT.md`; Codex's report `docs/codex-audit-2026-10-23.md`
  supersedes the earlier R11/full-scale/grounding conclusions. Follow-through rows (F2, F5, F9) under round 3.
- **Firmware**: Codex's plan (`docs/flashing-and-test-plan.md`) F1, F2, F3-F5, F7, F8 (estimate) done, plus F9 found on the
  way. Details and evidence: `docs/firmware.md`. Nothing flashed; no hardware exists.
- **Assessment / decisions**: `RELEASE_ASSESSMENT.md` (D-table). Not ready to order.

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
| r40 | silkscreen stroke 0.16 mm (skill minimum); fab export `gen/export_fab.py` -> `work/out/carrier/` (gitignored); `checks/jlc_rotation.py` and `checks/fab_files.py` | placement identical; 0 new (strict) / 0 open; JLC: 38 parts, corrections U1/U6 270, U4/U5 180, U2 shifted 0.725 mm; D2 paired by pin name (EasyEDA numbers the SS54 anode 1); run_all 20 checks 0 failed (current) |
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
