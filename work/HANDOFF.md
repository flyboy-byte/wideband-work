# HANDOFF — dense session context (read after STATE.md)

Written 2026-10-23 at the end of a ~500k-token session (Sonnet 5.5, then Opus 5.5); replaced the same day after the routing session. This is the "halfway tier":
more than memory, less than the transcript. It holds what STATE.md and docs/ don't: run history, tool quirks,
half-finished threads. Replace it (don't append forever) at the next handoff; durable facts belong in STATE/docs.

## Verify first, don't assume
- `git -C ~/projects/wideband-work status` / `git log --oneline -15` (branch `analog-out`; `master` == upstream
  mck1117/wideband at 2bb80d2; remote is named `upstream`; never push).
- `cd work && python3 checks/run_all.py`: expected now: module DRC 11 (upstream), module ERC 0, carrier DRC 26 (all
  upstream's except 3 unconnected), **`drc_vs_upstream` 0 new / 3 unconnected**, carrier ERC 0, self-check 17/17, drift clean.
  `python3 checks/drc_vs_upstream.py -v` lists the open pairs.
- Firmware: `cd firmware && make -j12 BOARD=f0_module` (bootloader built once already). App 20,900 B of 25,596; RAM `.heap` 0 B.

## The one thing in progress: carrier PCB routing
`python3 work/gen/gen_carrier_pcb.py` (~1.5 min) = greedy place (TARGETS order) → `anneal()` (seed env `SEED`, default 4)
→ nets from schematic → GND fan-out vias → +5V tap vias on upstream's top +5V track → keep-out aids → Freerouting
(clearance 0.25 at export, neck-down off) → `finish_routes.finish()` grid A* for what is left → delete aids → fill → stitch.
Env knobs for sweeps: `SEED`, `PASSES`, `ROUTE_CLEARANCE`, `TOP_NO_TRACKS` (JSON boxes), `FINISH_IGNORE` (rule areas the
finisher may ignore, default `top_no_new_tracks_1`, the box around the regulator caps). Freerouting log: `work/gen/freerouting.log`.

Last raw output (seed 4, committed board):
```
DRC vs upstream: 0 new violations, 3 unconnected
  open: Pad 1 [/AOUT_OA] of U6 @62.52,80.00 / Track [/AOUT_OA] @63.47,75.53
  open: Track [/VREF3] @57.46,81.24 / Pad 5 [/VREF3] of U4 @55.44,80.95
  open: Track [/AOUT_F2] @61.40,83.39 / Pad 3 [/AOUT_F2] of U6 @62.52,77.47
finisher: "no path" for these three: walled in by routes Freerouting already laid
```
Seed sweep (finisher on): seeds 1-10 → open 6,4,4,3,6,7,4,6,?,5; new violations 0 only on 2,4,5,7,8.

Run history (one change per row):
| Run | Change | Result |
| --- | --- | --- |
| r1-r5 | hand placement → nearest-legal-spot placer; netclass 0.25; mask web 0.1; cutout/edge keep-outs; top keep-out over 12V_RAW | 3 open + GND islands. **Root cause found later:** the placer pushed D5/C16 ~17 mm and JP2 ~16 mm from their targets |
| r6 | GND fan-out vias (10 of 16 pads) | 13 open: fan-out didn't address the real cause |
| r7 | annealing placer (net length + distance to existing copper) | 217 → 181 mm; all analog nets routed; CAN_H/+5V open; top tracks cut GND at C1/C2 |
| r8 | route clearance 0.25, top tracks banned everywhere | 0 new, 10 open (bottom-only too tight, as r4) |
| r9-r11 | ban box only around caps; keep +5V feed (no room: placer fails); +5V tap vias | 0 new, 5-7 open |
| r12 | 0402 passives, 1N4148WS (schematic change) | net length 169 → 141; still 5 open |
| r13 | seed sweep 2-8 | best seed 7: only AOUT_OA open (C15/R8 on opposite sides of two upstream sensor tracks) |
| r14-15 | crossing penalty; feedback nets weighted ×3; neck-down off | no better (5-9) |
| r16 | grid finisher, may use top near caps | **0 new, 3 open (seed 4)**: committed |

Next, in order:
1. Rip-up in the finisher: when a pair has no path, remove the new (unlocked) tracks of the blocking net(s) in a window
   around U6/U4, route the blocked pair first, then re-route the removed ones. Or route the op-amp's own nets (AOUT_OA,
   AOUT_INN, AOUT_F2, VREF3) with the finisher *before* Freerouting, locked, so the router works around them.
   The second is simpler; try it first.
2. If still short: drop the CAN terminator (R10/JP2, optional feature we added) to free area; ask the owner in STATE.
3. Then renders (top/bottom) and look; `drift.py record` both files; STATE stage update; review page; BOM/CPL; JLC
   two-sided cost; audit pack.

## Design facts a cold session would otherwise re-derive (all sourced in docs/)
- Analog out: module pad SEL_1 = PB1 = TIM3_CH4 (AF1, ST open pin data), shares the pump-DAC timer (46.9 kHz,
  1024 steps). PA8 is NOT usable (TIM1_CH1 = complement of heater TIM1_CH1N). SEL pads were a 3-state CAN-ID strap;
  SEL_1 strap dropped, SEL_2 kept and also = test mode when low at power-up.
- f0 RAM is full (no runtime allocation, so OK); no new threads; aux output updated from the CAN TX thread.
- Passives 0402 except R6 (68k Extended in 0402), R8/R9 (fault/surge, flagged for audit), C16/C17 (18 V rail). D3/D4 1N4148WS SOD-323.
- Carrier stage: 100k pull-down → 74LVC1G125 on REF3030 3.000 V → 2× 3.3k/100n → LM2904 ×1.68 (68k/100k), dual loop
  (DC fb after 330R, Cf 1 nF from op-amp out) → 330R → 1N4148WS clamps → J3-5; J3-7 = GND (signal ground).
  LM2904 supply: LSU_Heater+ → 1k → 18 V zener + 10u 50 V + 100n (TVS D1 is SMCJ30CA, rail can reach ~35-48 V).
- Stability sim: `work/sim/stability.sh` (TI model SNOM268 in work/sim/models/, gitignored): feedback-after-R oscillates
  at 10/47 nF; dual loop Cf 1 nF clean 1 pF-47 nF.
- Curve compiled in: 10 AFR = 0 V … 20 AFR = 5 V (Hondata's stated standard). Invalid lambda → 0 V (owner may change).
- Board can't grow: case.STL outer 47.5×44 around the 40×36.5 board; analog stage on the BOTTOM; module footprint has
  bottom courtyards on its header rows and an Edge.Cuts cutout x48.76-56.76 y72.84-78.30.
- Upstream carrier silkscreen was for an older module (TX/RX/nRESET); generator relabels to AOUT/TEST/VBAT.

## Tool quirks learned (also folded into the pcb-design skill 2026-10-23)
- pcbnew Python (KiCad 10.0.7): delete with `board.Delete(item)` from a collected list (Remove while iterating broke
  GetTracks); `fp.Flip(pos, pcbnew.FLIP_DIRECTION_LEFT_RIGHT)`; `fp.SetField('LCSC', x)` then
  `fp.GetField('LCSC').SetVisible(False)`; rule areas: `ZONE.SetIsRuleArea(True)` + SetDoNotAllow*; zone fill
  `pcbnew.ZONE_FILLER(board).Fill(board.Zones())`. Lots of harmless "Debug: Adding duplicate image handler" on stderr.
- Freerouting 2.5.0 headless: `java -Djava.awt.headless=true -jar ~/.local/share/freerouting/freerouting-2.5.0.jar
  -de b.dsn -do b.ses -mp 40 --gui.enabled=false`.
- kicad-cli: `sch upgrade` / `pcb upgrade` (netlist unchanged, verified); `pcb render --side bottom` (bottom view is
  mirrored); `sch export svg` + `rsvg-convert -b white -w 2400` to look; `magick … -crop` to zoom.
- JLC parts API (POST selectSmtComponentList) → `componentLibraryType` base/expand, stock, describe.
- KiCad 10 pcbnew: `GetBoardPolygonOutlines(poly, True)` needs the second arg; pads with no number (paste apertures) report
  no copper: filter with `IsOnCopperLayer()`. Freerouting 2.5.0 accepts `--router.automatic_neckdown=false`; it stops by itself
  when the score stalls ~10 passes (hard-coded, `-mp` only caps it) and counts upstream's 0.2 mm gaps as violations at 0.25.
- zsh: `VAR=x time cmd` is a parse error that kills the whole compound command, heredoc edits included.
- clangd diagnostics in firmware files are noise (no compile DB); `make` is the truth.

## Owner (Logan) — how to work with him (also in memory)
- Wants autonomy on "keep going": don't stop per step; put questions + chosen defaults in STATE.md.
- Hands-on tuner (K20Z3/FlashPro, carbs); don't explain ECU basics; Honda side is settled — don't revisit.
- Learning project: build and test it ourselves, not buy; cost-aware; reviews on phone; bench = multimeter + iron
  only (no scope, no bench supply); JLC places SMD, he hand-solders THT/connectors.
- Tests and audits concentrate on circuits, heater drive, control loops, firmware.
- Combined everything into this one repo on purpose; no extra folders/forks.

## Do not re-raise
Buying a ready-made controller; forking lambda-x2 or wideband-F103 (F103 single-channel is abandoned; lambda-x2's analog
out is the same circuit); narrowband simulation output; the Honda pin/ground details (in docs/carrier.md); the CAN-ID
strap trade-off (CAN-set ID still works); separate repos.

## Open questions (owner), with the default in use
- Output while sensor invalid: 0 V (reads 10 AFR). - Flashing method: keep module Tag-Connect pads reachable (works for
  SWD or rusEFI CAN). - Bring-up tests A1-A3 in docs/carrier.md: unconfirmed. - JLC two-sided assembly cost: unchecked.
