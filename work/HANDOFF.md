# HANDOFF — dense session context (read after STATE.md)

Written 2026-10-25 (Opus 5.5) after answering round 7. Replaces the earlier 2026-10-25 version (in git history).
Replace it at the next handoff.

## Verify first, don't assume
- `git status`: clean except `hardware/board_carrier/~board_carrier.kicad_pro.lck` (KiCad lock; `drift.py check` said
  no drift on 2026-10-25). `git branch --show-current` must say `analog-out` (Codex once left this checkout on its
  review branch). `master` = upstream mck1117/wideband; `upstream` push disabled; `origin` = public fork. Push allowed.
- `cd work && python3 checks/run_all.py`: **27 checks, 0 failed, 2 advisory** (raw upstream DRC, owner decision D2).
  Reviewers use `--report DIR`. The run rewrites timestamps in STATE.md and `checks/out/`: commit or `git checkout` them.
- Firmware: `cd firmware/boards/f0_module/bootloader && ./build_bootloader.sh`, then `make -C firmware -j8 BOARD=f0_module`.
- Sims (TI model in `sim/models/`, not committed): one at a time under `nice`.

Last raw output (2026-10-25, after the round 7 answers):
```
  R9 C844867: 0.480 W at 38.9 V clamp, rated 0.75 W (64%, if Rth <= 110 K/W)
  D5 C173425: 0.382 W at 38.9 V clamp, rated 0.5 W (76%, case under 93 C)
surge budget: 0 problem(s)
release gate rounds: 4/4 right            (old gate judged: Round 5; new: Round 7)
27 checks, 0 failed, 2 advisory failed, 0 skipped
```

## Where things stand (2026-10-25)
- **Board**: r41 layout, unchanged since 2026-10-24; R3 4.7k, R9 C844867. Fab candidate `work/out/carrier/` (26 BOM
  lines, 8 Extended). Not released; nothing ordered. Revisions used: none.
- **Firmware**: unchanged in behaviour since 2026-10-24.
- **Audits**: rounds 1-7 in `AUDIT.md`. **Round 7** (Codex/Astra, PR #3, merged with a merge commit): no BLOCKER or
  BUG; verdict "yes for a supervised first prototype, not a qualified automotive/fault-survival product". R7-S1 RISK
  (surge is a conditional budget: R9 Rth, D5 case under 93 C, the TVS clamp is for a 10/1000 us pulse) answered in
  wording; R7-S2 (the LM2904 is on VOP12, not +5V; A8 now measures the whole +5V load per state) and R7-S3 (headers,
  `--report` in setup, swap rule keeps power/pulse/thermal rating) fixed. It added 19 sampler/heater latency tests in
  its folder.
- **Found while answering**: `release.py` read the oldest round (last heading). Fixed here and in the skill
  (dotfiles c4a93a6), with `checks/test_release.py`.
- **Recommendation stands**: no more routine desk reviews; next review after bench data (A1-A8).
- Cousin (sidewinderzz): no activity since 2026-10-24 21:43 UTC.

## Next, in order
1. **Owner picks the first revision name** (none used; e.g. `carrier-a`, or `v1.0`). Then
   `python3 gen/export_fab.py && python3 checks/run_all.py`, commit, and
   `python3 checks/release.py <rev> out/carrier/carrier-gerbers.zip out/carrier/carrier-bom.csv out/carrier/carrier-cpl.csv out/carrier/not-fitted.csv`.
   Then fill `fab/<rev>/README.md`, add the rev to "Revisions used" in STATE.md, commit. The module files (`out/module/`)
   are upstream rev C and go in the same order.
2. **Order** (owner, money): `docs/ordering.md`. Edge rails for C11 (R6-S4); placement preview Q1 (module) and D2
   (carrier); `checks/bom_stock.py 5` on the day. About $180-215 for 5 + 5 (`ROADMAP.md`).
3. **Owner purchases**: HiLetgo ST-Link V2 + TC2030-IDC-NL + jumpers, LSU 4.9 + Bosch 1 928 404 669 plug kit,
   Molex 36792-1201. Bench tests: `docs/carrier.md` A1-A8, W1, H1-H6.

## This session (2026-10-25, after the first handoff of the day)
| Item | What | Evidence |
| --- | --- | --- |
| Round 7 | verified R7-S1..S3 against nets and datasheet figures; AUDIT "Round 7"; PR #3 merged | `AUDIT.md` |
| R7-S1 | `surge_budget.py`: -1 % R9, thermal conditions printed; `carrier.md` "conditional budget" | checker output above |
| R7-S2/S3 | +5V load list, A8 per-state whole-board current, REVIEW/AUDIT headers, `--report` in setup, swap rule | `review_docs.py` passes |
| Release gate | highest round number; audit folders and check scripts aren't design changes | `checks/test_release.py` (fails on the old gate: no `latest_round`) |

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
- Astra's review branches start from the commit it reviewed, not our latest: merge them (`--no-ff`), they don't
  fast-forward. Check scope with `git diff --name-only $(git merge-base analog-out B) B`.
- `release.py` takes the highest `### Round N` in AUDIT.md (rounds are listed newest first) and needs a `Commit:` line in it.

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
