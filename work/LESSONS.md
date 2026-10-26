# Lessons — rusEFI wideband

Every mistake caught on this board, with when and what caught it. At bring-up and after each order, propose the ones
that would help any board as a line for the `pcb-design` skill (see its "Lessons back to the skill" section).

2026-10-23 Codex audit lessons (not yet sent to skill):
- Geometry metrics must survive track-list permutation. The old gap count joined unrelated segments and overcounted
  short tracks; order-regression tests caught it. Use length-weighted samples and label heuristic limits explicitly.
- A current-limiting resistor is not a rail clamp. Account for powered-off injection and guaranteed sink current.
- Calibration cannot overcome actuator saturation. The full-scale load/tolerance budget must precede a trim claim.
- Record failed model convergence, then try a bounded ramp from a convergent operating point. Four full-scale cases
  then ran successfully; this expands typical-model evidence, not fault/temperature qualification.

| Date | Stage | What went wrong or nearly did | What caught it | General? | Sent to skill |
| --- | --- | --- | --- | --- | --- |
| 2026-10-23 | Requirements | Claimed module SEL pads were unused by firmware; the grep output was cut by `head -12` before the f0_module match | Re-check of the plan by a second model reading `port.cpp` | Yes: don't treat absence in truncated output as evidence | 2026-10-23 |
| 2026-10-23 | Requirements | Counted module pads from the carrier-side symbol (14) instead of the module netlist (16) | Netlist export during the re-check | Yes: count pins from the board's own netlist, not a symbol drawn for another board | 2026-10-23 |
| 2026-10-23 | Requirements | Proposed PA8 for PWM without checking which timer channel it shares; it is the heater's TIM1_CH1 complement | Re-check reading `io_pins.h` and the AF table | Yes: check timer and channel sharing before reusing a pin for PWM | 2026-10-23 |
| 2026-10-23 | Checks | `kicad_check.py` wrote every board's report to the same `checks/out/drc.json`, so a two-board project kept only the last | Noticed when reading reports | Yes: skill script fix (report named after the file) | 2026-10-23 |
| 2026-10-23 | Parts | Proposed taking op-amp feedback after the output's series resistor (to cancel load error) without checking stability; with TI's LM2904 model it oscillates at 10 nF and 47 nF of cable | `work/sim/stability.sh` with the maker's SPICE model | Yes: simulate any op-amp stage that drives a cable with the maker's model, across cable capacitance, before choosing the feedback point | 2026-10-23 |
| 2026-10-23 | Layout | Said the bottom layer had no copper and removed 18 GND stitching vias; upstream's GND pour is on both layers (unfilled in the file), so the vias joined the pours | DRC unconnected items after refill | Yes: check every zone's layer set before calling stitching vias useless | 2026-10-23 |
| 2026-10-23 | Layout | A new top-side track cut upstream's 12V_RAW pour in two | DRC unconnected (12V_RAW zone to itself) | Yes: when adding to an existing board, keep new tracks off other nets' pours (rule area during routing) | 2026-10-23 |
| 2026-10-23 | Layout | Freerouting 2.5.0 necked tracks to 0.15-0.19 mm (below the 0.2 mm rule), ignored the module's inner Edge.Cuts cutout and the 0.5 mm board-edge clearance | DRC track_width / copper_edge_clearance | Yes: widen after SES import; give the router keep-out rule areas for cutouts and the edge, remove them after | 2026-10-23 |
| 2026-10-23 | Layout | Upstream carrier silkscreen labels module pads TX/RX/nRESET; the current module has SEL_1/SEL_2/VBatt_Sense there | Comparing the bottom render with the module's own .kicad_pcb pad nets | Yes: check silkscreen pin labels against the mating board's pad nets | 2026-10-23 |
| 2026-10-23 | Layout | The nearest-legal-spot placer moved three parts 16-17 mm from their targets without saying so; five routing runs then chased "congestion" | Reading the placer's own printout after a fix made things worse | Yes: print each part's distance from its target and flag big moves; place by net length (annealing) rather than nearest spot | 2026-10-23 |
| 2026-10-23 | Layout | Exported to Freerouting with 0.25 mm clearance on a board whose existing copper is spaced at 0.2 mm: the router counted 116 violations before routing and lost room | `Auto-routing pass` lines in the Freerouting log ("N unrouted and M violations") | Yes: read the router's per-pass log; export clearance must not be stricter than the existing copper | 2026-10-23 |
| 2026-10-23 | Layout | Freerouting stops by itself when its score stalls for ~10 passes; raising `-mp` changed nothing | Same log ("has not improved ... Stopping") | Yes: `-mp` only caps passes; vary the placement (seeds) instead of adding passes | 2026-10-23 |
| 2026-10-23 | Layout | Footprint pads with no number (paste apertures) reported as obstacles in a clearance check | Debug print of the pads hit | Yes: filter pads with `IsOnCopperLayer()` | 2026-10-23 |
| 2026-10-23 | Layout | Freerouting finished all but 1-3 connections, different ones per run, on a dense extension area | Seed sweep | Yes: route the leftovers with a small grid finisher and judge by DRC; smaller passives (0402) where ratings allow free the most area | 2026-10-23 |
| 2026-10-23 | Process | The handoff file named the wrong next step (it gave my reading, not the raw placer output) | The next session's first fan-out run got worse | Yes: a handoff carries the last raw output, not only its interpretation | 2026-10-23 |
| 2026-10-23 | Layout | Routing a dense stage's nets one at a time (any order) walled in a different net each time | r17-r19 results | Yes: route the group together with negotiated routing (PathFinder: rip up, raise the cost of shared cells each round) | 2026-10-23 |
| 2026-10-23 | Layout | The finisher, the fan-out and the tap vias put 9 vias inside SMD pads of their own net; DRC doesn't flag that | New `checks/via_in_pad.py` | Yes: a via-in-pad check in every routed board's checks; via placers keep clear of all SMD pads, own net included | 2026-10-23 |
| 2026-10-23 | Layout | A GND pour piece under the op-amp held U6's ground pins but touched the main pour on neither layer; DRC showed only "zone to zone unconnected" | Union of pour pieces through vias and through-hole pads | Yes: after filling, find pour pieces not joined to the main one and join each with a via or a routed track; treat it as a real open, not a DRC quirk | 2026-10-23 |
| 2026-10-23 | Layout | The last open connection looked like a placement problem; scoring candidate fixes on a scratch copy (10 s each) showed the real cost: the new track cut the ground pour on both sides (a floating pad, a starved thermal pad) | `checks/whatif_route.py` + `drc_vs_upstream.py --pcb` | Yes: a what-if harness (candidate tracks on a copy, scored by the stage's own measure) beats a 4 min regeneration per idea; fold the winner into the generator | 2026-10-23 |
| 2026-10-23 | Process | A handoff said the open pair was D3 to +5V; the DRC listed a different pair (same island) each run | `drc_vs_upstream.py -v` vs the handoff | Yes: name the net island (a component/pad list), not one of the pairs DRC happens to print | 2026-10-23 |
| 2026-10-23 | Tools | `pkill -f` / `pgrep -f` with a script name matched the shell running them and killed the call; a "background task completed" notice was for the launcher, not the detached job | Exit code 144; empty log | Yes: kill by PID; wait on a DONE marker in the log | 2026-10-23 |
| 2026-10-23 | Tools | Upstream's gtest Makefile found `firmware/build/obj/*.o` through its search path and treated ARM objects as up to date | Link error "cannot find build/obj/pid.o" | No (this repo only): move `firmware/build` aside for the host tests | 2026-10-23 |
| 2026-10-23 | Process | I called a CAN-thread stall a "freeze forever" from reading the call name; the code had a 100 ms timeout, so the real effect was a 9 Hz output | Reading `can_helper.cpp` before changing it | Yes: read the called function before writing a finding about it | |
| 2026-10-23 | Firmware | A macro defined in a board header was invisible in a file that did not include `port.h`; the `#ifdef` silently took the old branch (build passed, size unchanged) | A temporary `#error` probe and the flash size delta | Yes: prove a new `#ifdef` is live with a `#error` probe or a size change | |
| 2026-10-23 | Layout | Weighting one net in the placer (to pull C17 in) moved the whole placement: 6 open connections and the placement-specific D3 link stopped applying | r33 run | Yes: placement-specific fixes need a "still applies" check after every placement change; one placement knob per run | |
| 2026-10-23 | Process | The release gate counts the two raw DRC runs (upstream's own errors) as failures, so it can never pass on an extended upstream board | Reading `release.py` | Yes: with a baseline board, gate on the baseline-subtracted check (owner decision) | |
| 2026-10-23 | Layout | A size limit (case.STL) was taken from upstream's files and never asked; it cost 33 routing runs on a too-small board | Owner: "what case. i do cad" | Yes: ask the owner before treating a file in the repo as a limit (AGENTS.md rule 7) | |
| 2026-10-23 | Layout | The placer scored a bypass cap by its net's half-perimeter, which doesn't care where the cap sits inside the net: C17 ended 6.1 mm from its pin | Measured pad distances | Yes: tie each bypass/feedback cap to its pin as a weighted pseudo-net, and start it on the right side of the chip (bottom-side parts are mirrored) | |
| 2026-10-23 | Layout | The CAN terminator placed beside the output's corridor pulled CAN_L 0.3 mm alongside the output for 6.8 mm; DRC was clean | New `checks/layout_review.py` | Yes: measure noisy/sensitive net spacing after every routing change | |
| 2026-10-23 | Docs | carrier.md said J3-7 is tied to GND "at one point near the output stage"; the board never did that | Reading the board's pads against the doc | Yes: check design claims in docs against the board file, not the generator's intent | |
| 2026-10-23 | Firmware | Upstream's bootloader bounded CAN writes by a hand-typed 26 KiB while the linker gave the app 25 KiB, and never checked offset + length; the right size sat in a linker symbol, used wrongly in a commented-out line (`__appflash_size__ / 1024` reads memory; the value is the symbol's address) | Codex source-extraction harness (F1) | Yes: take partition bounds from linker symbols by address, check offset then `length <= size - offset`, and give every guard test must-accept cases plus a mutant of the old bug | |
| 2026-10-23 | Firmware | A `.cpu cortex-m3` line in a shared assembly file overrode the f0 build's `-mcpu=cortex-m0`: the fault handler compiled to Thumb-2 and would lock the M0 up; the build gave no warning | Writing the package vector check, then objdump, then QEMU's Cortex-M0 | Yes: for every MCU core in a build, disassemble hand-written assembly and check it against that core's instruction set; test fault paths on an emulated core of the same architecture | |
| 2026-10-23 | Firmware | Test mode computed its 10 s step from `TIME_I2MS(chVTGetSystemTime())`; the f0's system time is 16 bits at 10 kHz and wraps every 6.55 s, so it never stepped. It built, and reading the code looked right | Host test with a fake clock typed from the board's own chconf.h, then run against the old code | Yes: any elapsed-time logic longer than the tick counter's wrap uses the 64-bit timestamp; host fakes take type widths from the real config | |
- 2026-10-24 Twelve parallel ngspice runs of TI's LM2904 model, each saving every node (about 1 GB per run), ran the 14 GB
  machine out of memory while other builds were running; the OOM kill took the session's terminal with it (likely the
  crash the night before as well). Caught by: the kernel log (`journalctl -k`). Fix: `.save` only the measured nodes
  (about 14 MB per run), one run at a time, `nice -n 19`, and look at `free -h` before starting heavy work on a shared machine.
- 2026-10-24 Ramping the op-amp supply from 0 V made one TI-model run take over 10 minutes; a fixed supply with only the
  input ramped takes 0.5 s. Use Codex's ramp (fixed rails, input step from 1.0 V).
- 2026-10-24 Every board since about r26 had two same-net vias with holes 0.225 mm apart (r36 GND, r37 +5V: a pre-placed
  tap or fan-out via plus the router's own), which would drill into each other. KiCad rates hole_to_hole a warning, and
  `drc_vs_upstream.py` compared errors only, so "0 new violations" hid it for a dozen runs. Caught by: reading the
  warning-level DRC during the silkscreen pass. Fix: the delta check counts fab-relevant warning types too
  (FAB_WARNINGS), and the generator merges close same-net vias after routing. Skill lesson candidate: a DRC gate must
  include warning types that matter to the fab, not only errors.
- 2026-10-24 JLC/EasyEDA pad numbering can differ from KiCad's for the same package: C22452 (SS54, SMA) numbers the
  anode 1, KiCad's D_SMA numbers the cathode 1. A rotation table found by pairing pads by number would have placed D2,
  the reverse-polarity diode, backwards (board dead on power-up). Caught by: `checks/jlc_rotation.py` comparing EasyEDA's
  symbol pin names with the schematic's, confirmed by the cathode band in EasyEDA's footprint. Fix: pair pads by pin
  function (names, else the cathode band), number only for parts without names. Skill lesson candidate.
- 2026-10-24 Upstream's exported BOM/CPL were older than its board (different TVS and Schottky, missing caps, old
  positions). Caught by: comparing the board's LCSC fields with the export, then `git log` on both. Never take fab
  data from an export without checking its date against the design files.
- 2026-10-24 A fresh clone is not the working copy: it has no local `master` (four checks did `git show master:`), no
  fab candidate (`work/out/` is ignored), no bootloader object (the app links it), and `.gitignore` had dropped every
  reviewer's raw output with the packs (`work/audit/`). Caught by: cloning into a scratch folder and running every
  check before asking an outside reviewer. Fix: `checks/upstream_ref.py`, setup steps in `REVIEW.md`, only packs
  ignored. Do the clone test before every outside review.
- 2026-10-24 A boot-time default nobody looked at: R3 100k was meant to hold the output at 0 V during boot, but the
  MCU's own pull-up on the same pin (set in both board.h files, upstream's choice for the strap) won, and the output sat
  at full scale for the bootloader's 0.8 s. Caught by: the outside reviewer reading board.h next to the schematic. Fix:
  check every "default state" claim against every driver of that node, including the MCU's internal pulls, in the
  bootloader as well as the app (`checks/boot_level.py`).
- 2026-10-24 Tool traps in one afternoon: `bc` can't read `3.3e-07` (ngspice prints it; a column came out as amps
  instead of microamps); `pkill -f <name>` matched its own shell; Python's urllib got a 403 from easyeda.com where curl
  is answered; a `with open(p,'w')` that reads `p` in the same expression empties the file; a check that compares
  demangled names (`CanTxThread(void*)`) with plain ones never matches. Do arithmetic in awk/python, name the PID, fetch
  with curl, and test an exclusion list against real names.
- 2026-10-24 TI's LM2904 model can't solve its operating point when the supply comes through a resistor (R9 1k): every
  stepping method fails. Start the transient with `uic` and the supply capacitor charged (`.ic`), and let it settle;
  a switch shorting R9 for 1 ms gave the same answer.
- 2026-10-24 LCSC warehouse stock is not JLC assembly stock (LM2904: 112 vs 219,277). Check stock with JLC's own parts
  API (`checks/bom_stock.py`), and check the upstream module's BOM too: two of its parts were out at JLC.
- 2026-10-24 An outside agent given a review brief (Codex, round 4) waited for a go-ahead, stopped after a first pass,
  and ran out of credits before writing up its second pass; the best finding (the heater bug) survived only because
  the owner saved the transcript. A brief needs numbered tasks with a "done" line each, an explicit "start now, don't
  wait", write-up and commit after every task, and a stop-at-a-quarter-budget rule (`review/TASKS.md`).
- 2026-10-24 The review pack copied files by basename, so the module's `README.md` and `not-fitted.csv` overwrote the
  carrier's: a blind reviewer never saw the carrier's not-fitted list. Caught while rewriting the docs. Pack builders
  must refuse a name collision. Docs that quote numbers (the check count) need a check that compares them with the
  repo (`checks/review_docs.py`).
- 2026-10-25 A static stack checker that "cuts loops through indirect calls as artefacts" hides exactly the recursion
  it exists to find (Codex R6-S6). Over-approximating indirect targets is sound only if every loop that results still
  fails; narrow the targets from the source instead, cross-checked against what each caller loads.
- 2026-10-25 ngspice can abort a transient, exit 0 and print finite zeros for a window it never reached (Codex R6-S8);
  "exit 0 and the numbers parse" passed it in all three wrappers. Have each deck print its last time point and require
  it to reach the stop time. A sim's "before" level must be settled before the step (R6-S7).
- 2026-10-25 A general-purpose 250 mW resistor in a load-dump path: the continuous power during a clamped 400 ms dump
  was 190 % of rating. Budget every part between a TVS-clamped rail and a clamp with the TVS's clamping voltage, not
  the nominal rail (`checks/surge_budget.py`).
- 2026-10-25 Codex ran its review in the designer's own checkout and left it on `review/astra-2026-10-25`, so the
  designer's next edits landed uncommitted on the reviewer's branch (caught by an empty `git diff HEAD...branch`).
  Reviewers work in a `git worktree` of their own (REVIEW.md, route B).
- 2026-10-25 `release.py` judged "the last round" by the last `### Round` heading, but AUDIT.md lists rounds newest
  first, so the gate read round 5 (and refused for a missing commit line, the right answer for the wrong reason). Caught
  while answering round 7. The gate now takes the highest round number (`checks/test_release.py`). Its file filter also
  counted reviewers' audit folders and check scripts as design changes, which would have demanded a re-audit after
  every review merge.
- 2026-10-25 Round 7 caught the designer listing the LM2904 as a +5V load in the backfeed answer: its supply pin is on
  VOP12. Read the net from the netlist before counting a part as a load.
- 2026-10-25 Reviewer worktrees (`../wideband-review-*`) were left in `~/projects` after their PRs merged; the owner found
  them. REVIEW.md now has the designer remove them after each merge.
