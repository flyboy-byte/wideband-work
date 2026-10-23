# HANDOFF — dense session context (read after STATE.md)

Written 2026-10-23 at the end of a ~500k-token session (Sonnet 5.5, then Opus 5.5); replaced twice the same day; this version is from the end of 2026-10-23. This is the "halfway tier":
more than memory, less than the transcript. It holds what STATE.md and docs/ don't: run history, tool quirks,
half-finished threads. Replace it (don't append forever) at the next handoff; durable facts belong in STATE/docs.

## Verify first, don't assume
- `git -C ~/projects/wideband-work status` / `git log --oneline -15` (branch `analog-out`; `master` == upstream
  mck1117/wideband at 2bb80d2; remote is named `upstream`; never push).
- `cd work && python3 checks/run_all.py`: expected now: module DRC 11 (upstream), module ERC 0, carrier DRC 26 (all
  upstream's), **`drc_vs_upstream` 0 new / 1 unconnected**, `via_in_pad` 0 new, carrier ERC 0, self-check 17/17, drift clean.
  `python3 checks/drc_vs_upstream.py -v` lists the open pairs.
- Firmware: `cd firmware && make -j12 BOARD=f0_module` (bootloader built once already). App 20,900 B of 25,596; RAM `.heap` 0 B.

## The one thing in progress: carrier PCB routing, one connection short
`python3 work/gen/gen_carrier_pcb.py` (~4 min) = greedy place (TARGETS order) → `anneal()` (SEED default 7) → nets from
schematic → GND fan-out vias (+ one for D3's +5V pad) → +5V tap vias on upstream's top track → keep-out aids →
**`finish_routes.negotiate()`** (PathFinder over PREROUTE nets; LOCAL_BOX limits big nets to a corner) → Freerouting
(clearance 0.25, neck-down off) → `finish_routes.finish()` for leftovers → delete aids → GND islands removed → stitch →
`join_gnd_pieces()` (via or routed track to the main pour). Checks: `checks/drc_vs_upstream.py -v`, `checks/via_in_pad.py`.

Last raw output (committed board, 6d294ae):
```
DRC vs upstream: 0 new violations, 1 unconnected
  open: Track [+5V] on F.Cu @63.29,80.90 / Track [+5V] on B.Cu @59.20,78.15   (D3 clamp diode to +5V, ~5 mm)
via in pad: 0 new, 0 upstream
```

Run history after the first handoff (r1-r16 are in git history of this file):
| Run | Change | Result |
| --- | --- | --- |
| r17-r19 | finisher pre-routes the stage's nets one at a time, locked, in various orders | each order walls in a different net (AOUT, then AOUT_F2/+5V) |
| r20 | **negotiated routing** (PathFinder: shared cells cost more each round, history cost, rip-up) | 12/12 local nets in 8 rounds, all signals routed; GND cut off at C2/C6 |
| r21-r23 | 0.5 mm free ring round top-side SMD GND pads (bottom ring blocked U6's escape, so top only) | 12/12, only D3 +5V + GND islands |
| r24-r25 | +5V whole branch / LSU_Heater+ into negotiation | worse (4 nets stuck in conflict over 80 rounds) |
| r26 | seed sweep 1-10 with negotiation | seed 7 best: 2 open (LSU_Heater+ branch, D3 +5V) |
| r27-r28 | D3 +5V fan-out via; keep LSU_Heater+ branch (worse: changes obstacles) → reverted; LSU_Heater+ negotiated in a LOCAL_BOX | 1 open (GND piece) |
| r29 | GND island removal + `join_gnd_pieces` (via, else routed track) | **0 new / 0 open**: but 9 vias in SMD pads (new check) |
| r30 | vias kept out of all SMD pads (finisher, fan-out, taps); CAN and D3 +5V in LOCAL_BOX | 0 new, 1 open (D3 +5V): committed 6d294ae |
| r31 | seeds 1-2; then +5V weight 4 in placement | worse (6, 9 open): reverted |

Next, in order:
1. D3 → +5V: move D3 by hand in TARGETS next to the +5V top-track tap (around 63-64, 81), or swap D3's role: clamp to
   the REF3030 input cap C11's +5V pad (same net, sits in the stage). Then re-run seed 7 only.
2. Fix C17 (op-amp bypass) 4.5 mm from U6 pin 8: weight VOP12 or pin it next to pin 8. Silkscreen overlaps (R3/C12, U5/C11).
3. Renders → look → review page → BOM/CPL → JLC two-sided quote → audit pack + Codex round → release gate.
Notes: runs take ~4 min now (negotiation); a 10-seed sweep is ~45 min, so prefer targeted changes. `pkill -f` with the
script name kills your own shell command; kill by PID.

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
