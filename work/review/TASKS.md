# Review tasks: round 7 (the round 6 fixes)

Written 2026-10-25. Round 6 (Codex, `audit/astra-2026-10-25/`) found two checker bugs that let a failure pass, plus
one surge risk; all three are fixed, and so is a stability-sim timing issue. This round checks those fixes and the
two risks still open. It is short on purpose: round 6 covered the rest, so don't redo it (its coverage table and
evidence are in its folder). Record every task in `FINDINGS.md`, even one you skipped, so we can see what was covered.

File names are the review pack's (`INDEX.md` maps each to its repo path). With the repo, the paths are under `work/`.

**How to work** (round 4 nearly lost its best finding because it ran out of credits before writing it up):
- Start at TK1 and keep going without waiting for a reply. Nobody is watching live: the owner reads the result later
  on his phone. Ask nothing you can decide yourself; write the assumption in the finding instead.
- After each task, add its row to `FINDINGS.md`. With git, commit it on your review branch, and push if you are allowed to.
  A half-finished review that is written down is worth far more than a finished one that isn't.
- When about a quarter of your budget is left, stop starting tasks. Finish the verdict and the coverage table, commit and push.
- Run the checks with `python3 checks/run_all.py --report <your folder>`, which leaves the designer's files alone.
- Going past this list is welcome (theory, circuits, anything that looks wrong). Put it under TK99.

| ID | Area | Question (answer it yes or no, with numbers) | Effort |
| --- | --- | --- | --- |
| TK1 | Stack checker | Is the `NARROW` target table complete and sound, so the stack estimate is a real upper bound? | M |
| TK2 | Sim wrappers | Can any failed ngspice run still pass `completed.sh`, and is the stability rerun valid? | S |
| TK3 | R9 surge | Does the C844867 swap make R9 and D5 survive a clamped load dump, with numbers from the datasheets? | M |
| TK4 | Backfeed | 12 V on J3-5 pushes 13.6 mA into +5V. Is there a cheap fix worth making before the first order? | M |
| TK5 | Fab files | Is the R9 change right in the BOM, CPL and board, and is the edge-rail step enough for C11? | S |
| TK6 | Round 6 leftovers | Pick from round 6's PARTLY rows (power ramps, sensor-fault latency, thermal loop) if you have budget | L |
| TK7 | These docs | What was missing or unclear here, and what would have saved you time? | S |

Effort: S under 15 min, M 15-45 min, L longer (with a shell; reading-only takes about twice as long).

---

### TK1. The stack checker's indirect-call table

- **Why:** round 6 (R6-S6) showed the checker cut every loop through an indirect call as an artefact, so a real
  recursion through a function pointer passed. Now every loop fails, and five callers whose over-approximation made
  impossible loops get a target set read from the source.
- **Files:** `stack_estimate.py` (`NARROW`, `SAMPLER`), `test_stack_estimate.py`, `firmware.diff`.
- **Shell:** `make -C ../firmware -j8 BOARD=f0_module`, then `python3 checks/stack_estimate.py -v` and
  `python3 checks/test_stack_estimate.py`. `arm-none-eabi-objdump -d -C ../firmware/build/wideband.elf` shows each
  `blx` site.
- **Questions:**
  - For each `NARROW` entry, can the source reach a target the table leaves out? In particular, is `Sampler` the only
    `ISampler` and `HeaterController` the only `IHeaterController` in the f0 build, and does `adc_lld_serve_rx_interrupt`
    call anything other than the group's `end_cb`?
  - Are the cross-checks enough? They are: each caller's own literal-pool targets must be listed, every name must be
    address-taken, and a listed caller must make an indirect call.
  - The other 10 functions with indirect calls (27 `blx` sites) keep "every address-taken function". Is that still a
    sound over-approximation?
  - Interrupt nesting and `initloop` (constructors before `main`) aren't modelled. Does either matter on this part?
- **Done:** yes or no on "the 92 B worst margin is a real bound", with the reasons.

### TK2. Sim wrappers: completion check and stability timing

- **Why:** round 6 (R6-S8) showed an aborted transient exits 0 and prints zeros, and all three wrappers passed it.
  Round 6 (R6-S7) also showed the stability step came before the output settled.
- **Files:** `completed.sh`, `stability.sh`, `load_accuracy.sh`, `full_scale_corners.sh`, `test_sim_failures.py`,
  `stability.out`, `full_scale_corners.out`.
- **Shell:** `python3 checks/test_sim_failures.py`; the real sims need TI's model (`REVIEW.md`, setup).
- **Questions:** can a failed or partial run still pass, for example an abort message the grep misses, or `END` printed
  by a run that failed to converge? Is the 0.5 mV drift guard before the step tight enough, and does moving the step to
  3 ms change any conclusion in `carrier.md`?
- **Done:** a failure mode that passes, or a reasoned "none found".

### TK3. R9 and D5 in a load dump

- **Why:** round 6 (R6-S3): the 250 mW R9 would take about 0.44-0.48 W for about 400 ms with D1 clamping at 38.9 V.
  R9 is now C844867 (Vishay CRCW12061K00FKEAHP, pulse-proof HP series, 0.75 W per JLC's listing).
- **Files:** `surge_budget.py`, `carrier.md` (op-amp supply), `carrier-bom.csv`, `carrier-nets.txt` (`/LSU_Heater+`
  -> R9 -> `/VOP12`: D5, C16, C17, U6.8).
- **Shell:** `python3 checks/surge_budget.py`.
- **Questions:**
  - Is 38.9 V for 400 ms the right worst case for D1 (SMCJ24CA), given a real load dump's source impedance? A
    centrally suppressed alternator, or the battery connected, would be lower.
  - Does the Vishay HP datasheet's pulse or continuous rating cover it?
  - D5 (BZT52C18, 500 mW) takes 0.378 W. Is that within its rating once derated for board temperature?
  - If not, what is the smallest fix that keeps the 1206 and SOD-123 footprints?
- **Done:** survives or doesn't, with the datasheet numbers.

### TK4. Backfeed into +5V

- **Why:** round 6 (R6-S2), accepted under owner decision C1 (no survival requirement for 12-16 V on J3-5). 12 V on
  J3-5 gives (12 - 5 - 0.6) / 470 = 13.6 mA through R11 and D3 into +5V, and the LM78M05 (U2) can't sink.
- **Files:** `carrier-nets.txt`, `carrier.md` (bench test A8), `module-nets.txt`, `wiring.md`.
- **Questions:** what does the board draw from +5V (module, TJA1051, REF3030, LM2904, LEDs)? Is it reliably above
  13.6 mA in every state, including CAN idle and the bootloader? If not, how high does the rail rise, and which part
  fails first? Is there a fix that needs no layout change (a part value or a part swap), and would you make it before
  the first order?
- **Done:** a number for the load current, and a yes or no on fixing it now.

### TK5. Fab files after the R9 change

- **Files:** `carrier-bom.csv`, `carrier-cpl.csv`, `carrier-parts.txt`, `jlc_rotation.json`, `ordering.md`.
- **Shell:** `python3 checks/fab_files.py`, `python3 checks/jlc_rotation.py`, `python3 checks/bom_stock.py 5`.
- **Questions:** is R9 C844867 in the BOM, with the same footprint, position and rotation as before? Does the
  ordering page's edge-rail step settle C11 (body about 1.6 mm from the edge, R6-S4)?
- **Done:** yes or no for each.

### TK6. Round 6's PARTLY rows

Round 6 left these as PARTLY (`audit/astra-2026-10-25/FINDINGS.md`, coverage table):
- TK3: the output during power ramps and resets, not just the steady levels;
- TK4: how fast a disconnected sensor is detected;
- TK5: the heater's thermal loop, not just the control law;
- TK6: the TI model's start-up independence.

Take any that you can add evidence to, and say which.

### TK7. These review docs

Tell us what was missing, wrong or slow here. The next reviewer gets the fix.
