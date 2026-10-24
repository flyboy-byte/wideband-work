# HANDOFF — dense session context (read after STATE.md)

Written 2026-10-23, end of the session that closed the last routing connection (Sonnet 5.5). Replaces the earlier handoff of
the same day; its run table r17-r31 is kept below. This is the "halfway tier": more than memory, less than the transcript.
Replace it (don't append forever) at the next handoff; durable facts belong in STATE/docs.

## Verify first, don't assume
- `git status`, `git log --oneline -10` (branch `analog-out`; `master` == upstream mck1117/wideband at 2bb80d2; `upstream`
  push disabled; `origin` = public fork github.com/flyboy-byte/wideband-work, push only when the owner says).
- `cd work && python3 checks/run_all.py`. Expected: module DRC 11 (upstream), module ERC 0, carrier DRC 22 (all upstream's),
  **`drc_vs_upstream` 0 new / 0 unconnected**, `via_in_pad` 0 new, carrier ERC 0, self-check 17/17, drift clean.
- `cd firmware && make -j12 BOARD=f0_module` (builds; untested on hardware). Host tests: see "Tests" in `CLAUDE.md`
  (43 gtest cases pass; `test/googletest` submodule must be initialised; move `firmware/build` aside first).
- Report page: `cd work && python3 checks/report.py` then publish `work/report/index.html` with the Artifact tool, same path
  = same URL (https://claude.ai/artifact/YRsjXKGZKG5AFbwkcMuYZ4, private, owner's account).

## Later the same day (self-audit by Sonnet 5.5, reviewed by Opus 5.5 in AUDIT.md round 2)
- **Open first: D6** (round 2, O1): J3-5 has no resistor between the connector and the D3 clamp to +5V; a 12 V wiring fault back-feeds +5V.
  Recommended fix (owner to approve): 470R 1206 in series at J3-5, outside the feedback; needs schematic + regeneration + a new D3 link.
- `RELEASE_ASSESSMENT.md` (new, read it first): concept, audit path, confidence (about 75 %), findings R1-R7, owner decisions D1-D5.
- `AUDIT.md` round 1 = self-audit (low independence). Codex round still to do on `work/audit/carrier-d-2026-10-23/`
  (give Codex `work/audit/carrier-g-2026-10-23/` (includes round 2); carrier-d/-e/-f are older, ignore).
- Firmware: `firmware/can_helper.cpp` drops the CAN frame instead of waiting 100 ms when `AUXOUT_SEL1_PWM_CHANNEL` is set (no node on
  the bus would slow the analog output to about 9 Hz). f0_module and f1_dual build clean; +32 B flash, RAM unchanged.
- r33: `NET_WEIGHT['/VOP12'] = 2.5` to pull C17 toward U6 pin 8 moved the placement: 6 open connections, `close_d3_link` skipped. Reverted
  (generator and board back to bf13162; verified 0/0). C17 stays at 4.5 mm (accepted RISK R3).
- `release.py` cannot pass while the two raw DRC checks fail on upstream's own errors: owner decision D2.
- Build quirk: after switching `BOARD=` run `make clean`, else the link fails with stale objects (`EFLD1` undefined on f1_dual).

## What changed this session (r32)
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

## Next, in order
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
- Board can't grow (case.STL); analog stage on the BOTTOM; module cutout x48.76-56.76 y72.84-78.30. Passives 0402 except
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
trade-off; separate repos; keeping the deleted LSU_Heater+/+5V bottom tracks; negotiating the whole +5V branch.

## Open questions (owner), with the default in use
Output while sensor invalid: 0 V. Flashing method: keep Tag-Connect pads reachable. Bring-up tests A1-A3 in docs/carrier.md:
unconfirmed. JLC two-sided assembly cost: unchecked. Whether to publish the report page to anyone else: it is private.
