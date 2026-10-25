# Findings: Codex / Astra (owner-selected), 2026-10-25 — round 7

Reviewed: `18b6cef4c5ca249423fce5a9924ea7fc53124220` on `analog-out`. Mode B, full repo; prior rounds visible. Worktree `/home/logan/projects/wideband-review-astra`, branch `review/astra-2026-10-25b`.
Tools: shell, KiCad, ngspice + locally licensed TI model, ARM compiler, host compiler, QEMU. No hardware. Findings are checked from source/tests; designer conclusions are claims to verify.

## Verdict

Would I order these files as they are? **Yes for a supervised first prototype, after the existing order-day rail/placement checks; not as a qualified automotive/fault-survival product.** No new BLOCKER or BUG found in this targeted round. The two round6 false-PASS defects are repaired in the reproduced cases, and R9's nominal power overload is fixed.

This is not unconditional release approval: D1/R9/D5 survival remains a conditional voltage/thermal budget (R7-S1); +5V backfeed still has no guaranteed sink (accepted C1); C11 needs factory acceptance of the actual rail plan. Physical unplug latency, power ramps and the heater thermal plant remain unqualified. These limits are not new owner requirements or a reason to redesign automatically.

## Coverage (one row per task in TASKS.md; fill it in as you go, not at the end)

| Task | Status | Finding IDs | What I did (command, file, calculation) |
| --- | --- | --- | --- |
| TK1 Stack checker | OK | — | Fresh ELF, four regressions, all40BLX sites and five narrowed caller sets checked. Worst thread margin92B reproduced; startup/interrupt scope assessed in TK1-stack-review.md. |
| TK2 Sim wrappers | OK | — |26fixture verdicts correct; actual old abort logs and short/no-END cases rejected. Real25case stability sweep passes completion/baseline guards; E0%through10nF,9.2%at47nF. TK2-sims.md. |
| TK3 R9 surge | PARTLY | R7-S1 | R9 nominal overload fixed:0.480W with -1%R vs0.75W conditional rating. MDD D5 derating gives92.7C case ceiling for0.382W. Real400ms input envelope/board cooling unknown; TK3-surge-review.md. |
| TK4 Backfeed | PARTLY | R7-S2 | Source-checked loads:6.235mA typical subtotal excluding MCU/IO/LED/ADC; no guaranteed13.6mA floor. LM2904 is NOT on+5V. No pre-prototype swap recommended under C1; TK4-backfeed-review.md. |
| TK5 Fab files | PARTLY | — | R9 exact part/unchanged geometry verified;26BOM/38CPL,live stock26/26available. Canonical suite26checks:0nonadvisory failures,2accepted advisories,0skipped; report isolation verified. C11 rail acceptance still order-day gate. TK5-fab-review.md. |
| TK6 Round 6 leftovers | PARTLY | — | Added19ASan/UBSan cases using real f0 Sampler+heater:synthetic ESR fault invalidates526–576ms;DC step firstsample;ADCstall staysvalid2s(known watchdog scope). Physical unplug/ramp/thermal loop remain unqualified. TK6-sensor-latency.md. |
| TK7 These docs | OK | R7-S2,R7-S3 | Compared setup/hand-off/tasks/checker against source; proposed corrections in TK7-doc-feedback.md. No designer docs changed. |
| TK99 Beyond the list | NOT CHECKED | — | No separate whole-board re-audit: this round targets round6 fixes. Added latency cases belong to TK6,not counted twice. |

Status: OK = checked and found right; FINDING = see the table below; PARTLY = say what is left; NOT CHECKED = say why
(no tool, no time, no file).

## Findings

| ID | Task | Severity | Location | Evidence (numbers) | Smallest fix |
| --- | --- | --- | --- | --- | --- |
| R7-S1 | TK3 | RISK | checks/surge_budget.py:6-10; R9/D5/D1 | DOCUMENTED/CALCULATED:0.480W R9 requires thermal conditions; D5 0.382W exceeds its derated rating above92.7C case.38.9V clamp is specified at a short pulse, not an arbitrary400ms event. | Keep HP R9; qualify the survival claim and define input/thermal envelope before claiming automotive-surge qualification. Detail in TK3-surge-review.md. |
| R7-S2 | TK4 | NOTE | review/TASKS.md TK4; docs/carrier.md A8; AUDIT.md round6 R6-S2 response | MEASURED U6.8=VOP12,not+5V; its current cannot count as a5V sink. A8's module-branch-only measurement excludes carrier loads. No guaranteed minimum13.6mA established. | Correct load list; distinguish module current from aggregate U2 output and record operating states. Keep accepted C1 risk explicit. |
| R7-S3 | TK7 | NOTE | REVIEW.md setup/header; AUDIT.md header; docs/ordering.md:74 | DOCUMENTED headers still round6 while tasks are round7; setup omits --report. Resistor-swap wording could overlook R9's0.480W budget versus old0.250W part. | Synchronize baseline/round,show reviewer --report command,and require equivalent power/pulse/thermal ratings. TK7-doc-feedback.md. |

Severity: BLOCKER = don't order; BUG = wrong but workable; RISK = could bite (say when); NOTE = worth knowing.
Tag each piece of evidence: MEASURED (you ran it), CALCULATED (show the sum), DOCUMENTED (name the datasheet and page),
INFERRED (your reasoning). A finding without a number or a source is a NOTE.

## Checked and found right

TK1: MEASURED recursion fails and verbose mode terminates;4/4existing regressions pass. Fresh package app21616B,CRC984fc2b4. Source-checked narrowed targets support the current thread estimate;92B is not a whole-processor margin.

TK2: MEASURED26failure-fixture verdicts correct,actual aborted logs rejected,real25case stability sweep complete. As-built0%overshoot through10nF under nominal model conditions.

TK3/TK5: MEASURED exact HP R9 part in board/fresh BOM;unchanged geometry/CPL;26live BOM lines available. Full suite24passes+2accepted advisory failures,no skipped checks. No drift and reviewer protected reports unchanged.

TK6: MEASURED19additional ASan/UBSan stimulus cases against unchanged production f0 sampler/heater;assertions pass. They do not substitute for physical tests.

## Could not check

- Actual protected load-dump waveform/TVS energy and assembly thermal impedance: specify the input envelope and qualify thermal/pulse limits before promising survival.
- Minimum board current through all power/reset/CAN states,or first device to fail during backfeed: benign current measurements and a controlled fixture are needed. No uncontrolled12V output-fault test recommended.
- Factory-approved rail/panel/placement plan: obtain it at the quote,not from local geometry checks alone.
- Physical unplug latency,analog power ramps,heater thermal dynamics and model-startup independence: no hardware or validated sensor thermal plant available.
- Universal stack guarantee after source/target/compiler/interrupt changes: current table is manually checked for this pinned build.

## TK7: what would have made this review faster

See TK7-doc-feedback.md: synchronize round/baseline headers,show --report in setup,correct the+5V load list,and link exact thermal/pulse datasheets. Proposed corrections only; designer files remain untouched.
