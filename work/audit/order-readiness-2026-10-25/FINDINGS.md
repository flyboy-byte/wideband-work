# Ordering-readiness review — Codex, 2026-10-25

Reviewed `c07643c` on `analog-out`, released `work/fab/flyboy-o2-v1/` (release commit `a642c86`).
Independent worktree `review/order-readiness-2026-10-25`; audit-only changes. Template adapted to the owner's
new ordering focus, not another repetition of round 7 TK1–TK7. Shell, KiCad and public vendor data available.
Concurrent designer commit `a396bee` adds the owner's one-order-only requirement and holds the order for a first-run
risk pass; this review respects that hold. No purchase, upload, quote submission or design change.

## Verdict

**No, not with the current hand-assembly shopping list.** OR1 is a confirmed header-fit BUG. The released PCB files
are internally consistent, but that does not establish physical assembly with the named header. Resolve OR1 and
establish the OR2 programming-access route before lifting the owner's order hold; obtain the existing factory
DFM/placement acceptance before payment. No design change or new release has been made. This review does not
promise first-run function, automotive qualification or no-respin certainty.

## Coverage

| Task | Status | Findings | Evidence |
| --- | --- | --- | --- |
| O1 Frozen release integrity and provenance | OK | | `O1-release-final.log`, `release-sha256.json` |
| O2 Both boards' assembly mapping and module Gerber geometry | OK | | `O2-assembly.log`, `O2-module-geometry.log`, `O2-drc.log`, `O2-drift.log`, `O2-release-gate.log` |
| O3 Two-assembled stock and factory requirements | PARTLY | OR3 | 52/52 lines available; `ORDER-CHECKLIST.md`; job-specific DFM/preview not performed |
| O4 First-run recoverability and checkout handoff | FINDING | OR1, OR2, OR4 | `O4-header-fit.log`, `O4-interface-verified.log`, manufacturer drawings; `FIRST-RUN-RECOVERY.md` |

## Findings

| ID | Task | Severity | Location | Evidence | Smallest fix |
| --- | --- | --- | --- | --- | --- |
| OR1 | O4 | BUG — hold order | `work/ROADMAP.md:116`; carrier U3 pins 1–16; released PTH drill | MEASURED holes 0.762 mm; DOCUMENTED Hanxia C32713274 drawing SQ 0.64 mm and recommended hole 1.02 mm. CALCULATED diagonal 0.9051 mm, 0.1431 mm larger than nominal hole. All 16 released holes checked (`O4-header-fit.log`). | Select and dimension-check a compatible interconnect (including tolerances, current, standoff and programming access). If retaining this header, designer must change/review/release larger holes. Do not assume drilling plated holes is a safe repair. |
| OR2 | O4 | RISK | `work/docs/wiring.md:91–93`; module J2 / carrier cutout | MEASURED cutout 7.874 x 5.334 mm (docs round to 8 x 5.5). DOCUMENTED TC2030-IDC-NL body 9.906 x 6.096 mm (manufacturer sheet 2), too large to enter it. Pin protrusion may permit contact from outside; final stack/reach is UNKNOWN. Pre-flashing alone does not solve A1/W1 reflash after assembly. | Resolve actual interconnect/standoff and prove contact/guide-pin reach, or document an accessible alternative SWD connection before permanent joining. Not a claim that this cable definitely cannot work. |
| OR3 | O3 | NOTE | `work/docs/ordering.md:11–13,40`; `work/fab/flyboy-o2-v1/README.md:33`; `work/HANDOFF.md` next steps | DOCUMENTED old instructions point to candidates, stock-check five assemblies and use old pricing; current owner quantity is two per board. | Use the frozen-file, two-assembly checklist supplied here; designer updates canonical pointers. |
| OR4 | O4 | RISK | `work/docs/flashing-and-test-plan.md:76,157–159`; `work/ROADMAP.md:117` | DOCUMENTED H1/H2 still require an unspecified current-limited source and net-specific short checks; roadmap offers an adapter plus fuse, explicitly not a limiter. No hardware run yet. Under one-order-only intent, a destructive first-power fault is not covered by three bare spare PCBs. | Finalize the actual first-power source/settings/rail stop values before energizing. This is an existing readiness gap, not a newly demonstrated circuit defect. |

## Checked and found right

- MEASURED: all eight frozen upload/not-fitted files match RELEASE.json's hash prefixes; full SHA-256 stored separately.
- MEASURED: all 27 recorded check results have no non-advisory failure; available checked files match their recorded
  hashes, resolving gitignored candidate files to their frozen release counterparts. This verifies recorded results,
  not a fresh run of all 27 checks.
- MEASURED: no hardware, firmware or generator differences from audited `18b6cef` or released `a642c86`.
- MEASURED: all nine carrier Gerber layers and both drill files equal fresh KiCad exports after ignoring date/software
  metadata only. Module ZIP is byte-identical to upstream rev C; geometric correspondence is O2, not assumed.
- MEASURED: module's four copper layers, both masks and outline have identical geometric primitives to fresh exports,
  retaining polarity-batch order (gerbonara 1.6.3); both drill files have identical drill commands. Both silks have
  identical dark geometry; the released KiCad-9 files additionally subtract 169/25 clear polygons (top/bottom).
  Seven negative controls reject deletion of an object. This comparison is independent of aperture numbering and
  plotting order, which change between KiCad 9 and 10; it does not silently ignore copper differences.
- MEASURED: all 52 BOM lines, 95 placed references and nine not-fitted entries cover both boards exactly once.
  Values, packages, LCSC IDs (including the two module substitutions), CPL position/rotation/side match the boards
  and measured correction tables. No paste on the nine not-fitted footprints. Rotation sense still needs preview.
- MEASURED: fresh DRC delta 0 new/0 unconnected; no drift; release-round regression 4/4.

## Attempt log

- O1 first attempt stopped on absent gitignored candidate paths in a clean worktree; use frozen release equivalents.
- O1 second attempt matched all Gerber layers but drill date comment differed; explicitly ignore `; DRILL file` metadata.
- O1 final attempt passes; failed attempts retained, not evidence of a release defect.
- O4 interface first attempts incorrectly assumed board-level cutout lines and the docs' rounded dimensions.
  Measurement found one footprint-owned Edge.Cuts rectangle, 7.874 x 5.334 mm. Parser and report corrected to that
  native geometry; failed logs retained. This changes the measurement method, not the fit acceptance criterion:
  the actual body envelope must clear the actual opening, or reach from outside must be proven.

## Could not check yet

Factory placement preview, order-specific DFM acceptance, actual delivered boards and electrical bench behavior.
No new full firmware build, all-27 run, or analog simulation sweep: current hardware/firmware/generators are unchanged
from round 7, verified by git diff and release-input hashes; this pass specifically tested frozen fabrication,
assembly/procurement and recoverability. Those prior tests are retained evidence, not relabeled as freshly executed.
Exact final interconnect/tolerances and assembled cable reach remain open. A factory quote, checkout or order was
not created; public stock lookup does not reserve parts. Two assembled samples do not guarantee a working unit.

## Handoff

PR #4 contains only this audit directory. Designer: verify OR1, choose the smallest compatible interface fix and
resolve OR2 with it, then record your independent response in `work/AUDIT.md`. See `FIRST-RUN-RECOVERY.md` and
`ORDER-CHECKLIST.md` for the remaining before-order versus before-power actions. Do not silently edit v1 fab files.
The pcb-design workflow directed the frozen-file comparison and physical interface checks; PDF drawings supplied
the dimensions that exposed OR1. No design work was performed under either skill.

## OR1 manufacturer source

Hanxia drawing **HX PZ2.54-1x8P ZZ**, page 1/1, dated 2022/04/24; square-pin dimension and recommended PCB layout
visually inspected, not inferred from a product photo:
https://datasheet.lcsc.com/datasheet/pdf/85243369e68f3858b37abf71bad9b29e.pdf?productCode=C32713274
This is the exact part named in `ROADMAP.md`; no assertion that every possible 2.54 mm header fails.
