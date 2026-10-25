# Findings: <reviewer> (<model or person>), <date>

Reviewed: commit `<git rev-parse --short HEAD>` on `analog-out`. Mode: <A, the pack only | B, the full repo>.
Tools I could run: <shell yes/no, KiCad yes/no, ngspice + TI model yes/no, firmware build yes/no>.

## Verdict

Would I order these files as they are? **<yes / no>**: <one sentence why>.

## Coverage (one row per task in TASKS.md; fill it in as you go, not at the end)

| Task | Status | Finding IDs | What I did (command, file, calculation) |
| --- | --- | --- | --- |
| TK1 Stack checker | <OK / FINDING / PARTLY / NOT CHECKED> | | |
| TK2 Sim wrappers | | | |
| TK3 R9 surge | | | |
| TK4 Backfeed | | | |
| TK5 Fab files | | | |
| TK6 Round 6 leftovers | | | |
| TK7 These docs | | | |
| TK99 Beyond the list | | | |

Status: OK = checked and found right; FINDING = see the table below; PARTLY = say what is left; NOT CHECKED = say why
(no tool, no time, no file).

## Findings

| ID | Task | Severity | Location | Evidence (numbers) | Smallest fix |
| --- | --- | --- | --- | --- | --- |
| <initials>1 | TK? | <BLOCKER / BUG / RISK / NOTE> | <file:line, or ref and x/y mm> | <measured or calculated, with source> | <one change> |

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

<short list: what you verified, so the next reviewer can skip or re-check it>

## Could not check

<what, and what you would need>

## TK7: what would have made this review faster

<missing files, unclear instructions, wrong paths>
