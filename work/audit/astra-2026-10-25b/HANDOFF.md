# Round 7 handoff — 2026-10-25

Read FINDINGS.md first. Reviewed design **18b6cef4c5ca249423fce5a9924ea7fc53124220**, not a generated replacement. PR https://github.com/flyboy-byte/wideband-work/pull/3 targets analog-out from review/astra-2026-10-25b. All reviewer changes are in this directory; the designer records the round in AUDIT.md after verifying it, per REVIEW.md's sending-it-back section.

## Outcome

No new BLOCKER/BUG in the targeted round6-fix review. Suitable for a supervised first prototype after factory rail/placement confirmation,not an unqualified automotive/fault-survival release. TK1/TK2 repaired false-PASS cases reproduce correctly;HP R9 fixes the nominal overload. Complete coverage and limitations are in FINDINGS.md.

## Designer follow-through proposed (not implemented)

| ID | Severity | Location | Evidence | Smallest action | Suggested status |
| --- | --- | --- | --- | --- | --- |
| R7-S1 | RISK | surge_budget.py;D1/R9/D5 | R9 worst illustrative0.480W vs conditional0.75W;D5 derating ceiling92.7C case for0.382W;actual400ms TVS envelope unspecified | Qualify "survives" wording,retain HP part,and define envelope/thermal conditions before claiming survival | Verify and retain as conditional prototype risk;no new harsher owner requirement |
| R7-S2 | NOTE | TASKS TK4;A8;round6 response | LM2904 is on VOP12,not+5V;module-only current excludes carrier | Correct load inventory and measure aggregate+5V across benign states | Verify correction;backfeed C1 acceptance unchanged |
| R7-S3 | NOTE | REVIEW/AUDIT headers,setup,ordering substitution rule | Round6 headers vs round7 tasks;plain run_all writes status;generic250mW1206 would again be192%loaded | Synchronize baseline,use --report,protect equivalent resistor thermal/pulse ratings | Proposed doc cleanup |

Do not automatically change R11:2.2k cuts12V injection to2.91mA but raises required OA output at5V/4.7k from5.85→7.69V and does not guarantee power-off protection. No no-layout swap recommended before this prototype under accepted C1.

## Evidence and resumption

Per-stage commits: TK1 9838efb;TK2 3d6819d;TK3 35cd6d8;TK4 cb67854;TK5 929b9f8;TK6 aa0e545;TK7 is the commit adding this file. Full configured suite:26checks,0nonadvisory failures,2accepted raw-DRC advisories,0skips.70host+21aux tests;4stack fixtures;26sim failure verdicts;25real stability runs. Extra19sampler/heater stimulus cases pass ASan/UBSan. These are different evidence sets,not summed as identical "tests".

Run commands from repo root unless noted:

```sh
python3 work/audit/astra-2026-10-25b/capture.py TK6-latency python3 audit/astra-2026-10-25b/run_sampler_latency.py
cd work
python3 checks/run_all.py --report audit/astra-2026-10-25b/
```

The audit-only scripts document assumptions and reproduce calculations. Fresh worktree setup is still required:submodules,KiCad/ARM/QEMU tools,f0 build and exported candidates. Production ELF built with ULIBS=/tmp/wb-round7-package/bl/wideband_bootloader.o from the separately checked fresh package. `/tmp` package is ephemeral;use fw_package.py build to replace it after reboot. TI model stays locally licensed/gitignored,not in this PR. Run real sim decks from work/sim so .spiceinit sets ngbehavior=psa.

Candidate BOM/CPL/not-fitted snapshots and hashes are evidence,not released order files. C11 rail must extend the relevant handling edge and receive factory acceptance;stock and placement preview must be rechecked before payment. No order,flash,merge,publication or push to analog-out/main occurred.

## Paste-back resume block

> Round7 complete at PR#3,baseline18b6cef,review/astra-2026-10-25b. Read work/audit/astra-2026-10-25b/FINDINGS.md then HANDOFF.md. TK1–TK7 committed separately;all26configured checks finish with0nonadvisory failures,2accepted DRC advisories,0skips. No new BLOCKER/BUG;R7-S1 qualifies surge thermal/envelope claims,R7-S2 corrects LM2904/+5V load analysis,R7-S3 proposes doc fixes.19new real sampler/heater host cases add conditional latency evidence,not physical unplug qualification. Designer:verify findings before edits,record round in AUDIT.md,retain C1 and order-time C11 rails/placement gates. Do not merge/order/flash automatically.
