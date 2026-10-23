# HANDOFF — dense session context (read after STATE.md)

Written 2026-10-23 at the end of a ~500k-token session (Sonnet 5.5, then Opus 5.5). This is the "halfway tier":
more than memory, less than the transcript. It holds what STATE.md and docs/ don't: run history, tool quirks,
half-finished threads. Replace it (don't append forever) at the next handoff; durable facts belong in STATE/docs.

## Verify first, don't assume
- `git -C ~/projects/wideband-work status` / `git log --oneline -15` (branch `analog-out`; `master` == upstream
  mck1117/wideband at 2bb80d2; remote is named `upstream`; never push).
- `cd work && python3 checks/run_all.py` — expected now: module DRC 11 (upstream), module ERC 0, carrier DRC ~32
  (14 courtyard + 3 malformed courtyard + some copper_edge are upstream's; unconnected 7 is OURS), carrier ERC 0,
  netlist self-check 17/17, drift clean.
- Firmware: `cd firmware && make -j12 BOARD=f0_module` (needs `boards/f0_module/bootloader/build_bootloader.sh` once;
  submodules ChibiOS/libfirmware/openblt already initialised). Expect app 20,900 B of 25,596; RAM `.heap` 0 B.

## The one thing in progress: carrier PCB routing (`work/gen/gen_carrier_pcb.py`)
Run: `python3 work/gen/gen_carrier_pcb.py` (~2-6 min, Freerouting) or `--no-route`. Then DRC:
`kicad-cli pcb drc --severity-error --schematic-parity --format json -o X.json hardware/board_carrier/board_carrier.kicad_pcb`
and diff against upstream's baseline (upgrade `git show master:...kicad_pcb` in a temp dir, DRC it, compare
(type, sorted item descriptions)). Only NEW violations matter.

Run history (each row = one change and its DRC result):
| Run | Change | Result |
| --- | --- | --- |
| place1 | hand coordinates | parts overlapped the module's bottom courtyards and cutout; LCSC field printed on silk |
| place2-3 | placer (target + nearest legal spot), AREA fence x48.8-71.2 y67.3-90.5, deleted 2 low-current upstream bottom tracks (REROUTE), floorplan: op-amp right of cutout, buffer/REF/RC below, supply lower-left | fits; C17 and D5 a few mm from ideal (note for audit) |
| r1 | first route | 56 track_width (router default width), duplicate bottom GND zone (upstream GND zone already F+B), tracks hugging cutout, SC-70 mask bridges (board min web 0.25) |
| r2 | default netclass 0.25, mask min web 0.1, cutout keepout, no own zone | still track_width: Freerouting necks to 0.15-0.19 at pads |
| r3 | widen <0.2 after import, edge keepout strips, cutout keepout grown 0.35 (0.5 covered upstream top tracks) | new routing clean; but 12V_RAW pour split by a new TOP track, GND islands |
| r4 | top-layer track keepout over whole board, keepouts deleted after routing, island stitcher | 7 nets unrouted (bottom-only too tight) |
| r5 (current, committed) | top keepout only over the 12V_RAW zone bbox +0.5 | 3 unrouted (CAN_H at R10, a +5V piece, AOUT_F2) + GND islands; stitcher added 1 via |

Next steps, in order:
1. GND fan-out: before routing, give every new GND pad a via (short stub, via 0.6/0.3) where the TOP GND pour exists
   (not inside the 12V_RAW zone bbox), so islands don't depend on the stitcher. Or let the router route GND by
   exporting without the GND zone; first option is simpler.
2. More passes (`-mp 100`) and/or nudge targets (R10/JP2 nearer CAN pins at 51.25/62.5 and 54.75/62.5; AOUT_F2 path).
3. Loop until NEW violations = 0 and unconnected = 0; then renders (top/bottom) and look; then `drift.py record` both
   files; then STATE.md stage update.
4. Then: fit-check/review artifact page for the owner (owner profile wants phone review pages), BOM/CPL export,
   JLC two-sided assembly cost check, audit pack (`checks/audit_pack.py`).

## Design facts a cold session would otherwise re-derive (all sourced in docs/)
- Analog out: module pad SEL_1 = PB1 = TIM3_CH4 (AF1, ST open pin data), shares the pump-DAC timer (46.9 kHz,
  1024 steps). PA8 is NOT usable (TIM1_CH1 = complement of heater TIM1_CH1N). SEL pads were a 3-state CAN-ID strap;
  SEL_1 strap dropped, SEL_2 kept and also = test mode when low at power-up.
- f0 RAM is full (no runtime allocation, so OK); no new threads; aux output updated from the CAN TX thread.
- Carrier stage: 100k pull-down → 74LVC1G125 on REF3030 3.000 V → 2× 3.3k/100n → LM2904 ×1.68 (68k/100k), dual loop
  (DC fb after 330R, Cf 1 nF from op-amp out) → 330R → 1N4148W clamps → J3-5; J3-7 = GND (signal ground).
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
