# TK5 — R9 files correct; rails require factory confirmation

**R9 BOM/CPL/board correct? Yes. Edge-rail step closes factory acceptance? No, not until the quote/DFM confirms it.** It is a sensible pending remedy, not a reason to move the circuit automatically.

MEASURED `fab_delta.py` proves the complete carrier PCB at18b6cef equals round6's43cc114 PCB after exactly one replacement: LCSC C4410→C844867. All geometry, tracks and R9's1206 footprint are byte-identical. Fresh export row:1k,R9,R_1206_3216Metric,C844867. Position68.8000,-94.4000mm in CPL,top,270deg; PCB68.8,94.4mm,-90deg. Exact rows/hashes in TK5-delta.log and TK5-carrier-*.csv. Exporter measured38parts,4corrections,0problems and produced12Gerber/drill/job files. Its candidate is not a released order package.

MEASURED live JLC stock lookup (2026-10-25,read-only):26/26lines available for5boards; R9 exact model CRCW12061K00FKEAHP,15000available,9needed including attrition. Eight Extended lines; parts-only estimate$20.83, not a cart quote or total delivered price. TK5-stock.log and TK5-bom-stock.json preserve the response summary. Availability must be rechecked on order day.

MEASURED canonical `python3 checks/run_all.py --report audit/astra-2026-10-25b/` through run_checks_isolated.py: **26checks,0nonadvisory failed,2accepted advisory DRC failures,0skipped**. Includes fresh ARM build,70host tests,21aux tests,4stack fixtures,sim failure fixtures,38carrier/57module rotation checks,fab comparison,0new DRC/0open/0newvia-in-pad/no drift. `TK5-all.log`,`last_run.json`,rawDRC/ERC reports retained. Protected STATE.md,checks/last_run.json andchecks/out tree unchanged by the run (`TK5-isolation.json`). Round6's false-PASS cases are separately exercised in TK1/TK2, not inferred repaired merely from this green table.

## C11 / order-day action

DOCUMENTED [JLC assembly terms,DFM3](https://jlcpcb.com/help/article/terms-and-conditions-of-jlcpcb-assembly-service):minimum2.5mm **body-to-edge**, versus this C11's approximately1.60mm. [JLC rail instructions](https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order):minimum5mm rails intended to increase assembly clearance; rails ship attached unless removal is requested. Both pages read2026-10-25,last-updated9-Sep-2026.

INFERRED: a5mm extension on the **C11-adjacent edge** would provide about6.6mm to the new outer handling edge. Rails only on the other edges are not automatically the remedy. Factory routing/tab/depanelization clearance is still its DFM decision. `docs/ordering.md:31-36` correctly leaves that decision at the quote. Before payment retain the accepted panel/rail drawing and placement preview with C11 unobstructed; ask for removal if desired. No factory upload/order or paid quote was performed in this review. No new manufacturing blocker beyond that already accepted order-time gate is asserted.
