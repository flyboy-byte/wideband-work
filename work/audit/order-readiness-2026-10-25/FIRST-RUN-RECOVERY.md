# One-order first-run review — 2026-10-25

The owner's one-order requirement is recorded at concurrent designer commit `a396bee`. This audit cannot certify
zero respin risk without hardware. It can identify preventable failures and require a credible way to recover with
the tools available. Nothing here authorizes ordering or powering a board.

## Highest-value closure before committing money

1. **OR1: resolve the module interconnect.** The exact loose header in the shopping list is not nominally compatible
   with the released carrier holes. Manufacturer drawing: Hanxia HX PZ2.54-1x8P ZZ, SQ 0.64 mm, PCB hole 1.02 mm;
   released carrier holes 0.762 mm. The nominal 0.905 mm square diagonal exceeds the hole by 0.143 mm.
   The minimum-change option is a dimensioned compatible tail, not automatically a PCB respin. Designer must name
   an actual part and check maximum tail envelope against minimum finished hole, lead length, heater-current rating,
   stack height and programming access. A nominal diameter smaller than 0.762 mm alone is not a tolerance analysis.
   Do not force pins or drill plated holes after assembly: that is not a validated repair.
2. **OR2: prove the SWD recovery route with that stack.** The programmer must work after the module is joined to the
   carrier because A1 trim and W1 require reflashing. First flashing before soldering is necessary but insufficient.
   Retain access with a verified connector/stack or an explicitly planned alternate SWD connection, not a hope that
   desoldering both eight-pin rows will be easy. No implementation chosen by this reviewer.
3. **Get factory acceptance and placement preview.** C11's edge clearance is an already-known order condition, not a
   fresh circuit finding. A proposed rail solves nothing until the factory accepts its actual panel and handling plan.
4. **Complete the hand-fitted supply list and first-power method.** Two controllers require two J3 board connectors,
   matching harness parts, four compatible eight-pin interconnects, the chosen programmer/cable/jumpers, and the
   power-limiting arrangement. The MCU programming and sensor are not included in the PCBA BOM. Three bare spare
   boards per design are not useful replacements for failed 0402/fine-pitch assemblies with only an iron.

## SWD evidence and remaining uncertainty

DOCUMENTED primary drawing: [Tag-Connect TC2030-IDC-NL rev B, sheets 1–2](https://www.tag-connect.com/wp-content/uploads/bsk-pdf-manager/2019/12/TC2030-IDC-NL-Datasheet-Rev-B.pdf), visually read.
The cable maps contacts 1–6 straight to IDC pins 1–6. This resolves the old FROM MEMORY mapping claim in
`work/docs/wiring.md:70–79`; still verify the actual clone's labels, polarity and continuity before applying power.

The nose/body outline is 9.906 x 6.096 mm (0.390 x 0.240 in), larger than the carrier's measured
7.874 x 5.334 mm (0.310 x 0.210 in) cutout (`O4-interface-verified.log`; U3-owned Edge.Cuts rectangle).
The old generator comment rounds it to 8 x 5.5 mm; that is not the exact cutout. The **body cannot pass through that
opening**. This does **not** prove the cable is unusable: protruding contact/alignment pins could reach from outside
the carrier if the final standoff permits. The chosen interconnect/standoff is not established, so full insertion,
contact compression, alignment-pin engagement and neighboring-part clearance remain UNKNOWN. A section drawing or
physical fixture test with the actual cable and stack closes this; comparing contact-pad area alone does not.

MEASURED native board J2 nets: 1 +3V3, 2 SWDIO, 3 nRESET, 4 SWCLK, 5 GND, 6 unconnected; no paste on contacts.
The HiLetgo clone's 3.3 V output is not treated as target-voltage sense. Do not parallel unknown supply outputs.
Native board header row spacing and pitch are 25.4 mm and 2.54 mm on both boards; the hole-size mismatch, not pitch,
is OR1. Electrical net names on the module heater-source header differ because that source is joined to ground
through the carrier; do not mistake those different labels for a reversed header.

## Failure → recovery assessment

| Failure/unknown | What was actually checked | Recovery with owner's tools | Before-order / before-power closure |
| --- | --- | --- | --- |
| Wrong/stale fabrication files | MEASURED frozen hashes, all carrier layers, module copper/mask/outline/drill geometry | Not a reflash fix; wrong copper can require rework or respin | Use exact frozen files and save factory preview; passed local comparisons do not validate a different upload |
| Module header will not enter carrier | MEASURED/DOCUMENTED OR1 | Compatible tails can avoid PCB change; forcibly drilling plated holes is not approved | **Before order: named compatible part + tolerance and stack check** |
| No SWD contact after joining boards | Body/cutout dimensions known; final reach UNKNOWN, OR2 | Reflash is easy only while pads are accessible; removing 16 soldered pins is not a routine recovery assumption | **Before order: establish accessible stack/connection**; prove readback before permanent joining |
| Unprogrammed MCU / firmware defect | Prior round 7 package, host tests, stack checks; hardware startup never run | SWD readback/reflash; preserve config and option bytes | Stage exact combined bootloader/app image with hashes; verify identity/readback with sensor disconnected |
| Reversed/missing assembled active part | All 95 CPL entries match board/correction data; factory convention remains preview-dependent | Fine-pitch/0402 rework may exceed iron-only setup; second assembly is redundancy, not proof | Exact part matches, all polarity marks in factory preview, inspect delivered boards unpowered |
| Supply short or incorrect regulator voltage | DRC/previous circuit review; no real board measurement | Damage prevention is much easier than replacing ICs | **Before first power:** actual limited source, voltage/current setting, polarity check and rail-specific stop values; H1/H2 still draft |
| Meter/fuse mistaken for current limiter | `flashing-and-test-plan.md:76,157–159` still requires a selected limiter | A series ammeter measures current; a fuse limits fault duration, not current to a chosen safe value | Do not substitute a raw battery or adapter-plus-fuse for a reviewed first-power method |
| Output gain/offset wrong | Prior model/host results, A1 step protocol; no measurement yet | Compile-time trim + SWD if monotonic/load-compatible | Record 1/2.5/4 V before/after trim; keep SWD usable |
| Receiver loads/clamps output | Accepted R1 and low-output pull-up risk; target input resistance UNKNOWN | Calibration cannot cure saturation; R11 rework is accessible but needs verified value/stability | Do not promise universal 0–5 V accuracy. Measure chosen receiver/load and retain the existing acceptance decision |
| Sensor/heater wiring or loop fault | Prior host/latency tests; physical heater/loop not exercised | Reflash can fix software; burnt silicon/sensor is not guaranteed iron-recoverable | Continuity against terminal numbers; no ECU/sensor until power and recovery pass; no intentional battery-on-output fault tests |
| Main power-ground failure | Shared ground is accepted circuit fact | Wiring correction before damage; receiver-ground damage is not covered by this audit | Verify primary ground/crimp before ECU connection; do not open it as a test |
| Load dump / low-current +5V backfeed | Round 7 conditional calculation and owner acceptance, not qualification | Potential component damage, not assured recovery | Keep previous scope/conditions visible; no new claim of vehicle transient immunity |

## Designer handoff

Verify OR1 from `header_fit.py` and the manufacturer drawing before choosing a fix. Record the selected actual
interconnect and check OR2 at the same time. Update the shopping/wiring docs, then ask the auditor to re-check only
the changed interface/assembly plan. If board or fabrication outputs change, release a new revision through
`checks/release.py`; do not mutate `flyboy-o2-v1`. If a no-PCB-change interconnect closes both, demonstrate that
instead of respinning by default. The final factory preview and power-up measurements still cannot be delegated
to a desk-only PASS.
