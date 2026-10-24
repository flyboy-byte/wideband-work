# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Last updated 2026-10-23 (routing closed, r32). `AGENTS.md` is the authoritative, model-agnostic guide (evidence tags, subagents, Codex
audits) and wins over this file. Where this file and `work/STATE.md` / `work/HANDOFF.md` disagree, those win: they
hold the current state; this file holds orientation.

## What this is

`~/projects/wideband-work`, public at **github.com/flyboy-byte/wideband-work** (default branch `analog-out`). It is
three things at once, and the root `README.md` presents all three:

1. **A wideband O2 controller.** A fork of `mck1117/wideband` (MIT, the rusEFI LSU 4.9 controller: an STM32F042 module on a
   carrier board). It adds a **0-5 V analog output** so it works with any voltage input: Speeduino, a K20Z3 on
   Hondata FlashPro (datalogging only), a gauge for carb tuning. rusEFI CAN works as before.
2. **An AI-designed hardware project.** Schematic, PCB, firmware change and simulations were produced by Claude from
   code, with Logan directing.
3. **The worked example of the `pcb-design` skill's documented workflow** (`~/.claude/skills/pcb-design/WORKFLOW.md`,
   published in `flyboy-byte/scripts-docs-dotfiles`).

It's a learning project: build and test it ourselves, don't buy a ready-made unit. Nothing has been ordered or built.

## Start every session here

1. **Load the `pcb-design` skill**, and read its `WORKFLOW.md` (the loop, autonomy, the pause point).
2. Read `work/STATE.md` (stage, decisions not to re-ask, check results, open items), then `work/HANDOFF.md` (the
   last long session: run history, the last raw output, next steps, tool quirks). Both are snapshots: verify them.
3. Verify before trusting anything:
   - `git status`, `git log --oneline -10` (branch `analog-out`)
   - `cd work && python3 checks/run_all.py`
   - `cd firmware && make -j12 BOARD=f0_module`
4. Work the current stage (see "Where it stands"). At a natural stop: commit the best state, replace `HANDOFF.md`,
   update `STATE.md`, add lessons to `LESSONS.md`, give Logan a resume block.

## Where it stands (2026-10-23; check `work/STATE.md` for newer)

- **Firmware** (branch `analog-out`): builds. Analog output on module pad SEL_1 = PB1 = TIM3_CH4 (shares the pump-DAC
  timer, 46.9 kHz). Compiled-in curve 10 AFR = 0 V … 20 AFR = 5 V, 0 V while lambda is invalid. Bench test mode (SEL_2
  strapped low: 1.00/2.50/4.00 V steps) and trim constants. RAM is full to the byte, which is safe because nothing is
  allocated at runtime. Untested on hardware.
- **Carrier schematic**: generated, ERC 0, netlist self-check 17/17.
- **Carrier PCB**: generated and routed. **0 new DRC violations and 0 open connections** beyond upstream's baseline (r32), no vias
  in pads. Next: C17 to U6 pin 8, silkscreen overlaps, then audit (pack in `work/audit/`, Codex round) → BOM/CPL → JLC
  two-sided quote → `release.py`.
- **Assessment**: `work/RELEASE_ASSESSMENT.md` (concept, audit path, confidence, caveats, owner decisions) and `work/AUDIT.md` round 1 (self-audit).
- **Module board**: upstream's, unchanged (DRC 11 upstream errors, judged harmless or not yet: open).

## Commands

```sh
cd work && python3 checks/run_all.py              # every check; writes the table in STATE.md
python3 checks/drc_vs_upstream.py -v               # carrier DRC minus upstream's own errors, lists open pairs
python3 checks/via_in_pad.py                       # new vias in SMD pads
python3 checks/whatif_route.py [NAME] [--keep]     # candidate tracks on a scratch copy, scored by drc_vs_upstream (10 s each)
REV=carrier-d python3 checks/report.py             # rebuild work/report/index.html (status page), then publish it with Artifact
python3 gen/gen_carrier_sch.py [--check]           # regenerate the carrier schematic / netlist self-check
python3 gen/gen_carrier_pcb.py [--no-route]        # place + route the carrier (~4 min); env SEED (default 7)
python3 checks/drift.py check                      # owner's KiCad edits since the last generation (run before regenerating)
python3 checks/drift.py record ../hardware/board_carrier/board_carrier.kicad_pcb ../hardware/board_carrier/board_carrier.kicad_sch
sim/stability.sh                                   # LM2904 stability vs cable capacitance (needs TI model in sim/models/, gitignored)
cd firmware && make -j12 BOARD=f0_module           # firmware; also `BOARD=f1_dual` must still build

# upstream gtest suite (host build; CI runs it under ASAN, then valgrind with SANITIZE=no). 43 tests pass (2026-10-23)
git submodule update --init test/googletest        # not checked out by default
cd test && mkdir -p build/obj build/lst && make -j4 && ASAN_OPTIONS=detect_stack_use_after_return=1 build/wideband_test
build/wideband_test --gtest_filter='*Heater*'      # single test / suite
```

Test-build quirk: the test Makefile's search path resolves `build/obj/*.o` to `firmware/build/obj/` (ARM objects), so the
link fails with "cannot find build/obj/pid.o" while a firmware build exists. Move `firmware/build` aside for the test
build, then put it back. The `mkdir -p` is also needed (the dir rule isn't a prerequisite of the object rules).

## How the carrier PCB is generated (`work/gen/gen_carrier_pcb.py`)

The base is upstream's board from `master`, upgraded to KiCad 10, with every upstream track locked. New parts go on the
**bottom**: the top is full. (`case/case.STL` was treated as a size limit until 2026-10-23; the owner designs his own enclosure, so the board may now grow: see `work/STATE.md`.) The steps:
1. Greedy placement to targets.
2. **Annealing placement** by net length plus distance to existing copper.
3. Pad nets from the schematic netlist.
4. GND fan-out vias; +5V tap vias on upstream's top track.
5. Keep-out aids for the cutout, the edge and the 12V pour.
6. **Negotiated routing** (`finish_routes.negotiate`, PathFinder) of the analog stage's nets, locked.
7. Freerouting 2.5.0 joins the rest.
8. `finish_routes.finish` routes leftovers.
9. Delete the aids, refill, remove pour islands, join GND pour pieces.

Run history and what each change did: `work/HANDOFF.md`.

## Design in one paragraph (sources in `work/docs/`)

Module pad SEL_1 carries the PWM. On the carrier:
- 100k pull-down → 74LVC1G125 buffer powered from a REF3030 (3.000 V), so the PWM amplitude is the reference, not the
  MCU supply
- 2× RC 3.3k/100n
- LM2904 ×1.68 (68k/100k) with a dual-loop feedback: DC feedback after the 330R, plus 1 nF from the op-amp output. TI's
  model shows feedback after the resistor alone oscillates into cable capacitance.
- 330R → 1N4148WS clamps to +5V and GND → connector J3-5, with J3-7 as signal ground
- LM2904 supply: 12 V → 1k → 18 V zener, because the input TVS lets the rail reach about 35-48 V

Passives are 0402 except R6, R8, R9, C16 and C17.

## Rules

- Tag claims DOCUMENTED / REPORTED / INFERRED / FROM MEMORY / UNKNOWN and name the source (`AGENTS.md`).
- KiCad files are generated from code. Logan may edit them in KiCad: run `drift.py check` before regenerating and
  ask before overwriting an edit it lists.
- Fab files reach `work/fab/` only through `checks/release.py`. Ordering is Logan's call.
- After a placement or routing change, render it and look before reporting.
- Git: `upstream` = mck1117/wideband with its push URL disabled. `origin` = the public fork; push only when Logan says.
  `master` stays equal to upstream. Commit messages start with the area (`board_carrier:`, `firmware:`, `work:`).
- Tests and audits concentrate on circuits, power, heater drive, control loops and firmware.

## Logan

Hands-on tuner (K20Z3/FlashPro, carbs, Speeduino/rusEFI): don't explain ECU basics. Reviews from his phone. His bench
is a multimeter and an iron (no scope, no bench supply). JLC places the SMD parts; he hand-solders through-hole. On
"keep going" he wants autonomy: work through reversible steps, put questions and the default chosen in `STATE.md`,
and stop for money, deletion, overwriting his edits or publishing.

## Do not re-raise

- buying a ready-made controller
- forking lambda-x2 or wideband-F103
- a simulated-narrowband output
- the Honda side (settled: datalogging over the 0-5 V input; stock closed loop stays on the narrowband)
- the CAN-ID strap trade-off
- separate repos or folders
- keeping the deleted LSU_Heater+/+5V bottom tracks (worse, r9/r27)
- negotiating the whole +5V branch (deadlock, r24-r25)

## Layout

| Path | What |
| --- | --- |
| `firmware/`, `hardware/`, `case/` | Upstream code; ours differs on `analog-out` (`git diff master`) |
| `test/` | Upstream gtest suite for the firmware logic (PID, heater, sampling), unchanged |
| `work/STATE.md`, `HANDOFF.md` | Current state; dense hand-off |
| `work/REQUIREMENTS.md`, `parts_research.md` | Owner's answers and bring-up tests; sourced part facts |
| `work/docs/` | `analog-out.md` (facts F1-F16, attempts), `carrier.md` (design, stability, tests A1-A3), `firmware.md` |
| `work/gen/` | Schematic and PCB generators, `finish_routes.py` |
| `work/checks/` | Check scripts and `checks.json`; release gate; audit pack |
| `work/sim/` | ngspice decks |
| `work/LESSONS.md`, `AUDIT.md`, `ORDERS.md` | Mistakes caught; audit rounds; orders (none yet) |
| `work/renders/` | Pictures by stage |
