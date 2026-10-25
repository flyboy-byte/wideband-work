# Findings: Codex / Astra (owner-selected), 2026-10-25 — round 7

Reviewed: `18b6cef4c5ca249423fce5a9924ea7fc53124220` on `analog-out`. Mode B, full repo; prior rounds visible. Worktree `/home/logan/projects/wideband-review-astra`, branch `review/astra-2026-10-25b`.
Tools: shell, KiCad, ngspice + locally licensed TI model, ARM compiler, host compiler, QEMU. No hardware. Findings are checked from source/tests; designer conclusions are claims to verify.

## Verdict

Would I order these files as they are? **Not assessed yet**: review in progress.

## Coverage (one row per task in TASKS.md; fill it in as you go, not at the end)

| Task | Status | Finding IDs | What I did (command, file, calculation) |
| --- | --- | --- | --- |
| TK1 Stack checker | OK | — | Fresh ELF, four regressions, all40BLX sites and five narrowed caller sets checked. Worst thread margin92B reproduced; startup/interrupt scope assessed in TK1-stack-review.md. |
| TK2 Sim wrappers | OK | — |26fixture verdicts correct; actual old abort logs and short/no-END cases rejected. Real25case stability sweep passes completion/baseline guards; E0%through10nF,9.2%at47nF. TK2-sims.md. |
| TK3 R9 surge | PARTLY | R7-S1 | R9 nominal overload fixed:0.480W with -1%R vs0.75W conditional rating. MDD D5 derating gives92.7C case ceiling for0.382W. Real400ms input envelope/board cooling unknown; TK3-surge-review.md. |
| TK4 Backfeed | PARTLY | R7-S2 | Source-checked loads:6.235mA typical subtotal excluding MCU/IO/LED/ADC; no guaranteed13.6mA floor. LM2904 is NOT on+5V. No pre-prototype swap recommended under C1; TK4-backfeed-review.md. |
| TK5 Fab files | | | |
| TK6 Round 6 leftovers | | | |
| TK7 These docs | | | |
| TK99 Beyond the list | | | |

Status: OK = checked and found right; FINDING = see the table below; PARTLY = say what is left; NOT CHECKED = say why
(no tool, no time, no file).

## Findings

| ID | Task | Severity | Location | Evidence (numbers) | Smallest fix |
| --- | --- | --- | --- | --- | --- |
| R7-S1 | TK3 | RISK | checks/surge_budget.py:6-10; R9/D5/D1 | DOCUMENTED/CALCULATED:0.480W R9 requires thermal conditions; D5 0.382W exceeds its derated rating above92.7C case.38.9V clamp is specified at a short pulse, not an arbitrary400ms event. | Keep HP R9; qualify the survival claim and define input/thermal envelope before claiming automotive-surge qualification. Detail in TK3-surge-review.md. |
| R7-S2 | TK4 | NOTE | review/TASKS.md TK4; docs/carrier.md A8; AUDIT.md round6 R6-S2 response | MEASURED U6.8=VOP12,not+5V; its current cannot count as a5V sink. A8's module-branch-only measurement excludes carrier loads. No guaranteed minimum13.6mA established. | Correct load list; distinguish module current from aggregate U2 output and record operating states. Keep accepted C1 risk explicit. |

Severity: BLOCKER = don't order; BUG = wrong but workable; RISK = could bite (say when); NOTE = worth knowing.
Tag each piece of evidence: MEASURED (you ran it), CALCULATED (show the sum), DOCUMENTED (name the datasheet and page),
INFERRED (your reasoning). A finding without a number or a source is a NOTE.

### Two examples of the level we want (from earlier rounds)

- **Round 4, heater (BUG):** "`heater_control.cpp`: the effective heater voltage goes negative above the target
  temperature and is then squared into a duty. Feeding the host model a sensor at 806 C gives 65 % duty, at 840 C
  100 %, so a hotter sensor gets more heat. Fix: clamp the voltage at 0 before squaring." It has a location, a run
  with numbers, and a one-line fix.
- **Round 5, boot level (BUG):** "Both `board.h` files set PB1 as an input with its pull-up on (`board.h:335`,
  `bootloader/cfg/board.h:333`); the app only hands PB1 to TIM3 in `InitAuxDac()`. Pull-up 25-55k against R3 100k
  gives 2.13-2.64 V, a high at U4, so J3-5 sits at 5.04 V for about 0.8 s at every key-on, and indefinitely in the
  bootloader. Fix: R3 to 4.7k (0.52 V worst case), and/or a pull-down in both `board.h`." It cites the lines, does
  the sum, and names the condition that makes it matter.
- Not useful: "consider adding ESD protection to the output". Where, against what, and why is what's there not enough?

## Checked and found right

TK1: MEASURED recursion fails and verbose mode terminates;4/4existing regressions pass. Fresh package app21616B,CRC984fc2b4. Source-checked narrowed targets support the current thread estimate;92B is not a whole-processor margin.

## Could not check

<what, and what you would need>

## TK7: what would have made this review faster

<missing files, unclear instructions, wrong paths>
