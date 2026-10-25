# Checkout handoff — frozen flyboy-o2-v1, 2026-10-25

**HOLD: resolve OR1 header fit first.** This is an audit, not an order or a guarantee of first-run success.
Owner's current goal is one order, two complete controllers; no purchase was made here.

## Exact files and quantities

Use only `work/fab/flyboy-o2-v1/`, not `work/out/` or upstream exports. Verify full hashes against this audit's
`release-sha256.json`. Two separate PCB/assembly jobs in one cart:

| | Carrier | Module |
| --- | --- | --- |
| Gerber ZIP | carrier-gerbers.zip | module-gerbers.zip |
| BOM | carrier-bom.csv | module-bom.csv |
| CPL | carrier-cpl.csv | module-cpl.csv |
| Reference exclusions, not assembly BOM | carrier-not-fitted.csv | module-not-fitted.csv |
| Bare quantity / assembled quantity | 5 / 2 | 5 / 2 |
| Outline, mm (in), nominal | 40.0 x 51.5 (1.575 x 2.028) | 29.0 x 20.9 (1.142 x 0.823) |
| Copper layers / thickness | 2 / 1.6 mm (0.063 in) | 4 / 1.6 mm (0.063 in) |
| Assembly | Top only, 38 placements | Top only, 57 placements |

DOCUMENTED: release README, actual layer exports, `O2-assembly.log`, owner quantity in `STATE.md` at `c07643c`.
Use green FR-4 and obtain an Economic quote for the existing design; retain the chosen finish in the order record.
Do not confuse five bare PCBs with five assembled PCBs, or a panel count with a count of individual boards.

## Factory checks before payment

- Confirm outline, cutout, both/all four copper layers and plated/non-plated drills in the factory viewer.
- Request/confirm handling for the carrier's near-edge C11; the known body-to-edge distance is about 1.6 mm
  (0.063 in), below JLC's 2.5 mm (0.098 in) term. Rails are a proposed remedy, not demonstrated acceptance.
  Save the engineer's answer and panel/rail drawing; require that added tabs/rails avoid pads and parts.
- Economic capabilities support 2–50 assemblies, 2/4/6 layers and 10 x 10 mm minimum individual boards.
  Its page says rails/fiducials are not generally necessary, while the general terms say they are required.
  **Use job-specific confirmation, not a blanket claim that adding rails automatically makes C11 acceptable.**
  Standard fallback requires a larger handling envelope (70 x 70 mm); do not change service silently or assume
  its price matches Economic. These are factory handling dimensions, not a new enclosure/PCB-size requirement.
- Check all 26 BOM matches per job by exact LCSC number. Do not accept substitutions or omissions silently.
  Carrier R9 must stay **C844867 / CRCW12061K00FKEAHP**; generic 1k 1206 is not equivalent.
  Module R10 **C2087389 / ERA-3AEB61R9V** and C3 **C106862 / CC0402KRX7R9BB333** are the reviewed substitutions.
- Placement confirmation: carrier D2 cathode first, D3/D4/D5, all IC pin-1 marks and U2 tab; module Q1 tab first,
  then U2/U9/U1/U3/U5 and LED cathodes. Preview must match the released copper, not just the pretty board render.
  Any repo-side assembly-file correction requires regeneration/checks and a new immutable release, not editing v1.
- No programming service is selected/verified; expect blank MCU firmware. No functional power-on testing is promised.
- Capture the final quote, parts substitutions/omissions (prefer none), preview, DFM acceptance, options, totals,
  shipping/tax and order IDs. After authorization/payment, designer records actual uploaded files and order metadata.

## Live availability — not a price quote or stock reservation

MEASURED public JLC API, 2026-10-25: 26/26 carrier and 26/26 module lines available for two assemblies with the
checker's attrition quantities. Snapshots: `stock-carrier.json`, `stock-module.json`; logs include exact command.
Parts-only estimates: carrier **$10.41**, module **$23.27**, combined **$33.68**; exclude PCBs, setup, stencil,
loading, assembly, rails, shipping, taxes and any quote-specific attrition. Carrier 8 Extended, module 9 Extended.
Module MCU C69216 was the tightest stock: **199**, versus computed need **2**. Recheck at checkout; not reserved.

Re-run from `work/`:

```sh
python3 checks/bom_stock.py 2 fab/flyboy-o2-v1/carrier-bom.csv
python3 checks/bom_stock.py 2 fab/flyboy-o2-v1/module-bom.csv
```

Primary vendor sources read 2026-10-25 (summarized, not assumed from old project docs):

- [JLC assembly capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities): service dimensions,
  layer/thickness/quantity support, rails/fiducials distinction and default stack-up.
- [JLC assembly terms](https://jlcpcb.com/help/article/terms-and-conditions-of-jlcpcb-assembly-service), §§2,3,5:
  2.5 mm edge clearance, preview responsibility, no functional testing. Three unassembled spares can have reflowed
  tin on their pads; do not promise pristine bare boards. Two populated copies do not guarantee two working units.

## Scope fence

Prior electrical risks remain accepted/conditional as in round 7: this is not load-dump qualification or proof of
sensor-loop behavior. No PCB resizing, different controller architecture or enclosure gate is proposed here.
