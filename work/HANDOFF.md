# HANDOFF — dense session context (read after STATE.md)

## F7 done — 2026-10-23 (Claude Opus 5.5)

13 heater `Update()` tests (host suite 64/64). Standalone f0 assumes 13 V supply: D11 (module PB0 has the divider; RAM 0 B).
Remaining from Codex's plan: F6 thread cadence; circuit C1-C3, C7 (need owner answers: receiver load, endpoint tolerance,
fault survival requirement, grounding policy); owner decisions D1, D2, D7-D11.

## F8 estimate done — 2026-10-23 (Claude Opus 5.5)

`checks/stack_estimate.py`: all threads fit, smallest margin 80 B (pump), CAN TX 312/512. Needs an f0 build in
`firmware/build` (in-tree f0 needs `bootloader/build_bootloader.sh` first). Runtime high-water still for bring-up.

## F3-F6 done — 2026-10-23 (Claude Opus 5.5)

`test/aux_out/` (16 tests; `make -C test/aux_out run`, or `AUXOUT_SRC=` to test another version). Found and fixed F5:
test mode never stepped (16-bit system time). Curve moved to `aux_curve.h`; trim macros overridable with a static_assert.
Next: F7 heater coverage, F8 stack marks (needs hardware or a careful static estimate), F6 thread-loop cadence; circuit
C1-C3, C7. Owner decisions D1, D2, D7-D10.

## F2 and F9 done — 2026-10-23 (Claude Opus 5.5)

F2: `checks/fw_package.py build|check`, `checks/test_fw_package.py` (21 cases). Staged packages in `work/fw-build/<commit>/`
(gitignored). F9 (new, found writing F2): the f0 HardFault entry was Thumb-2, so a fault locked the M0 up instead of
resetting; fixed, proven on QEMU microbit (`checks/test_fault_entry_m0.py`, includes upstream's entry as a must-fail).
In-tree f0 builds need `boards/f0_module/bootloader/build_bootloader.sh` first (the app links its .o). Next: F3-F6
(aux-output host tests), then circuit C1-C3, C7. Owner decision D10 (watchdog).

## F1 done — 2026-10-23 (Claude Opus 5.5, after Codex)

Bootloader DATA guard fixed (`bootloader_bounds.h`); `audit_bootloader_bounds.py` updated to the new call site, now also
checks valid writes are accepted; 8 gtest cases; host suite 51/51 with LeakSanitizer on. Next per the plan: F2 (package
validator), F3-F6 (aux-output host tests; `auxout.cpp` is not compiled into the host suite yet), then C1-C3 and C7.
Host tests: absolute `BUILDDIR` (no moving `firmware/build`), see `CLAUDE.md`.

## Codex audit addendum — 2026-10-23

Flashing, host tests, emulator feasibility and meter-only bring-up: `docs/flashing-and-test-plan.md`.
Fresh native build: 43/43 pass with leak checking disabled (environment limitation). Absolute temporary BUILDDIR avoids
moving ARM build output. New `checks/audit_bootloader_bounds.py` reproduces F1 using actual source + recording flash stub:
48 cases / 10 unsafe accepts, no hardware access. Next: F1 fix, safe image packaging/validation, actual aux-output tests.
Plan contains Claude's bounded handoff; nothing was sent externally.

Read `docs/codex-audit-2026-10-23.md` and `AUDIT.md` round 3 first. Audited 34cd49d; no PCB/schematic/firmware changes.
New bounded reproducers: `checks/audit_analog.py` and `checks/audit_layout_order.py`.
Follow-up: order regression now PASSES; repaired checker flags a 6.8 mm PWM uncovered component (C7).
Ramped endpoint models succeed at 12 V/7.5 V and 100k/10k: use `audit_analog.py --full-scale`.
R11 limits but does not block back-feed; trim cannot restore a clipped
full-scale endpoint. The generic ECU sensor-ground instruction is withdrawn: that wire can carry heater current.
Next: resolve C1/C2/C3 electrically and inspect C7. C4's false metric is replaced with an explicitly limited component heuristic.
80R instead of 470R restores nominal 5 V into 10k, but raises the 16 V fault-current budget to 123.75 mA: not a standalone fix.
Original handoff retained below as history; its protection conclusions and zero-trigger layout signoff are superseded.

Written 2026-10-23 late, after r36 (board grown, R11 added; Opus 5.5 reviewing and continuing Sonnet 5.5's session). Replaces
the earlier handoffs of the day; the r17-r32 run table is kept below. Replace it at the next handoff.

## Verify first, don't assume
- `git status`, `git log --oneline -10` (branch `analog-out`; `master` == upstream mck1117/wideband at 2bb80d2; `upstream`
  push disabled; `origin` = public fork github.com/flyboy-byte/wideband-work, push only when the owner says).
- `cd work && python3 checks/run_all.py`. Expected (r36): module DRC 11 and carrier DRC 23 (all upstream's), **drc_vs_upstream
  0 new / 0 unconnected**, via_in_pad 0, **layout_review 0 triggers**, carrier ERC 0, self-check 18/18, no drift.
- `cd firmware && make clean && make -j12 BOARD=f0_module` (make clean when switching BOARD). Host tests: `CLAUDE.md`.
- Report page: `REV=carrier-e python3 checks/report.py`, publish `work/report/index.html` with the Artifact tool (same path =
  same URL https://claude.ai/artifact/YRsjXKGZKG5AFbwkcMuYZ4, private).

## This session, in order (read `RELEASE_ASSESSMENT.md` section 0 first)
1. Sonnet self-audit (AUDIT round 1), firmware fix in `can_helper.cpp` (drop CAN frame, don't wait 100 ms, on this board).
2. Opus review (AUDIT round 2): the 12 V-on-J3-5 fault path through D3 (O1), numbers corrected.
3. Owner: no case limit, function first, no assumed engineering decisions (AGENTS.md rules 7-8; memory feedback-function-first).
4. r34-r36: board grown 15 mm at the bottom (`GROW` in `gen/gen_carrier_pcb.py`, `grow_board()`), stage in the new strip,
   R11 470R 1206 (C4502) at J3-5 (schematic net `AOUT_J`), `REROUTE = []`, PREROUTE only the stage's own nets, bypass
   pseudo-nets (`BYPASS`, weight 8). `close_d3_link` no longer applies (prints "skipped"; dead, kept guarded).
5. New `checks/layout_review.py` (coupling, return path incl. coplanar GND, pour/stitching), in `checks.json`.
6. `sim/stability.sh` topology D (R11): 0-0.5 % overshoot, 0.46 % low into 100k.
7. Grounding analysis and D7 (`docs/carrier.md`), bring-up test A4 proposed.

| Run | Change | Result |
| --- | --- | --- |
| r36 | C17/C15 start targets on the correct (mirrored) side, bypass weight 8 | **0 new / 0 open / 0 via-in-pad / 0 review triggers**; C17 2.1 mm, C15 2.3 mm |
| r35 | CAN terminator to the strip's left end, output group under the corridor right of the cutout | 0/0; coupling clean; C17 6.1 mm (stuck above the chip) |
| r34 | board +15 mm, stage in the strip, R11, upstream tracks kept | 0/0 first try; CAN_L 0.3 mm beside the output for 6.8 mm (layout_review) |
| r33 | `/VOP12` weight on the small board | 6 open: reverted |

## Next, in order
1. Owner decisions: D7 (analog ground), D8 (mounting holes), D9 (stage on top = one-sided assembly), D1 (R9 1206), D2 (release gate).
2. Codex audit on a fresh pack (`checks/audit_pack.py carrier-h ...`, same file list as carrier-g plus `checks/layout_review.py` output).
3. Silkscreen pass (overlapping refs in the strip), BOM/CPL, JLC quote (owner approves money), `release.py`.

## Earlier: r32 (small board, superseded by r34-r36)
The one open connection (D3 clamp diode +5V pad, an island 4.2 mm from the +5V net) is closed, and the board regenerated:
`gen/gen_carrier_pcb.py: close_d3_link()` applies `checks/whatif_route.py: CANDIDATES['FIX_D3']` before the final pour fill:
1. +5V, F.Cu, 0.25 mm: via (60.10,78.15) -> (64.35,78.15) -> (64.35,80.50) -> (64.90,80.50), ends inside U2 pin 3 (+5V pad).
2. GND via 0.5/0.3 at (66.00,79.35) + 0.2 mm F.Cu tie to C1 pin 2 (that track cut C1 pin 2 off its pour).
3. C2 pin 2: solid zone connection (thermal spokes were starved by the same track).
It only applies when D3 pin 1 is at (59.20,78.15), i.e. the seed-7 placement; otherwise it prints "skipped".

Last raw output (regenerated board, 2026-10-23 18:33):
```
close_d3_link: D3 +5V linked to U2 pin 3 (top), C1 pin 2 GND via, C2 pin 2 solid
wrote hardware/board_carrier/board_carrier.kicad_pcb
DRC vs upstream: 0 new violations, 0 unconnected
via in pad: 0 new, 0 upstream
8 checks, 2 failed, 0 skipped      (the 2 failures are the upstream-baseline DRC runs: module 11, carrier 22)
```

## The method that found it (reuse it)
`checks/whatif_route.py` puts candidate tracks/vias/pad settings on a scratch copy of the board and scores each with
`drc_vs_upstream.py --pcb FILE` (~10 s, instead of the 4 min regeneration). Chain entries: `(net, layer, width, [pts])`,
`('via', net, x, y, dia, drill)`, `('padsolid', ref, pad)`. `python3 checks/whatif_route.py NAME [--keep]`.
Order of attempts (also on the report page): T1 route to U2 pin 3 (3 path shapes) -> closes it but floats C1 pin 2 and starves
C2 pin 2; T2 grid of GND via spots (31 run; 5 reach 1 violation); T3 C2 pin 2 solid -> 0/0; T4 into the generator, regenerate:
0/0 again; T5 looked at the render.

| Run | Change | Result |
| --- | --- | --- |
| r32 | `close_d3_link` (FIX_D3), found with whatif_route | **0 new / 0 open**, 0 new vias in pads (this session) |
| r30 | vias out of SMD pads; CAN and D3 +5V in LOCAL_BOX | 0 new, 1 open (D3 +5V): committed 6d294ae |
| r31 | seeds 1-2; +5V weight 4 in placement | worse (6, 9 open): reverted |
| r29 | GND island removal + `join_gnd_pieces` | 0/0 but 9 vias in SMD pads |
| r26-r28 | seed sweep (seed 7 best); D3 +5V fan-out via; LOCAL_BOX for LSU_Heater+ | 2 open -> 1 open |
| r24-r25 | whole +5V branch / LSU_Heater+ into negotiation | worse (deadlock) |
| r20-r23 | negotiated routing (PathFinder); free ring round top GND pads | 12/12 local nets |
| r17-r19 | one-at-a-time pre-routing, various orders | walls in a different net each time |
Runs r1-r16 are in this file's git history.

## Next steps as of r32 (superseded, kept for history)
1. **Audit** (nothing has been audited): pack is `work/audit/carrier-d-2026-10-23/` (gitignored, read-only; paste `PROMPT.md`
   first; `firmware.diff` is `git diff master -- firmware`). Hand-off text is in `AUDIT.md`. Give it to Codex, keep its raw output
   under `work/audit/`, add a round to `AUDIT.md` naming the auditor and commit. Check first: analog stage, power (R8/R9 0603,
   zener rail), **C1 bypass return now 0.5 mm via + 0.2 mm tie** (new, INFERRED fine).
2. Silkscreen overlaps (R3/C12, U5/C11) and C17 4.5 mm from U6 pin 8 (op-amp bypass; weight VOP12 or pin it). A placement change
   invalidates `close_d3_link` (coordinates) and the result must be re-measured; fallbacks if that happens: move D3 by hand in
   TARGETS next to U2 pin 3, or clamp to C11's +5V pad (same net, in the stage), then run seed 7 only.
3. Review page (`reference` in the skill) and BOM/CPL -> JLC two-sided quote -> `checks/release.py`. Ordering is the owner's call.

## Design facts a cold session would otherwise re-derive (sourced in docs/)
- Analog out: module pad SEL_1 = PB1 = TIM3_CH4 (AF1), shares the pump-DAC timer (46.9 kHz, 1024 steps). PA8 not usable.
  SEL_1 CAN-ID strap dropped, SEL_2 kept and = test mode when low at power-up. RAM full (no runtime allocation); update from the
  CAN TX thread; curve 10 AFR = 0 V … 20 AFR = 5 V; invalid lambda -> 0 V (owner may change).
- Stage: 100k pull-down -> 74LVC1G125 on REF3030 3.000 V -> 2x 3.3k/100n -> LM2904 x1.68, dual-loop feedback (DC after 330R + 1 nF
  from op-amp out) -> 330R -> 1N4148WS clamps -> J3-5; J3-7 signal ground. LM2904 supply: LSU_Heater+ -> 1k -> 18 V zener.
- (Until r33 the board was held inside case.STL; since r34 it is 40.0 x 51.5 mm.) Analog stage on the BOTTOM, in the strip; module cutout x48.76-56.76 y72.84-78.30. Passives 0402 except
  R6, R8/R9 (flagged), C16/C17.
- U2 pin 3 is a +5V pad (x 64.52-65.72, y 79.80-82.00); C1 = LSU_Heater+ / GND bypass; C2 = +5V / GND. The top corridor
  between C10 and U2 is 0.55 mm: a track through it kills the pour on both sides, which is what T1 showed.

## Tool quirks (also in the skill)
- Everything in the earlier list holds (pcbnew deletes, Freerouting flags, kicad-cli render/svg, zsh `VAR=x time`, clangd noise).
- **`pkill -f` / `pgrep -f NAME` match your own shell command** (exit 144 kills the call): kill by PID.
- Test Makefile (`test/`) resolves `build/obj/*.o` to `firmware/build/obj/` via VPATH: move `firmware/build` aside, and
  `mkdir -p build/obj build/lst` first.
- `kicad-cli pcb export svg --layers F.Cu,Edge.Cuts --mode-single --page-size-mode 2 --exclude-drawing-sheet` gives a board-fit
  SVG: with `rsvg-convert -w 4000` the scale is 99.9 px/mm from the board's top-left (39.975, 54.725), handy for crops.
- pcbnew in KiCad 10: `conn.GetConnectedItems(item)` takes no flags (call `board.BuildConnectivity()` first);
  `board.FindNet(name)`, not `GetNetInfo().GetNetItemByName`; `pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)`.
- A background task's "completed" notice can be for the launcher, not the detached job: grep its log for a DONE marker.

## Owner (Logan)
Autonomy on "keep going": reversible steps without stopping, questions + defaults into STATE.md; stop for money, deleting,
overwriting his KiCad edits, publishing, pushing. Hands-on tuner, don't explain ECU basics. Learning project. Bench: multimeter
and iron only. Reviews from his phone (hence the report page). JLC places SMD; he solders through-hole.

## Do not re-raise
Buying a ready-made controller; forking lambda-x2 / wideband-F103; narrowband simulation output; the Honda side; CAN-ID strap
trade-off; separate repos; ~~keeping the deleted LSU_Heater+/+5V bottom tracks~~ (superseded r34: all upstream tracks kept); negotiating the whole +5V branch.

## Open questions (owner), with the default in use
Output while sensor invalid: 0 V. Flashing method: keep Tag-Connect pads reachable. Bring-up tests A1-A3 in docs/carrier.md:
unconfirmed. JLC two-sided assembly cost: unchecked. Whether to publish the report page to anyone else: it is private.
