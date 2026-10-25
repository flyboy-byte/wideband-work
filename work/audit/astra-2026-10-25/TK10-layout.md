# TK10 layout measurements

MEASURED current PCB, no regeneration: TK10-drc.log0new/0unconnected;TK10-vias.log0new/0upstream vias-in-pad;TK10-layout.log0heuristic triggers. Its results are geometry, not solved return impedance.

Independent pcbnew pad-center distances:

| Supply pin | Capacitor supply pad | distance | cap GND to nearest GND via |
| --- | --- | --- | --- |
|U4.5 (49.7625,98.25)|C12.1(48.08,98.4)|1.689mm|0.900mm at(47.4644,99.2315)|
|U5.1 (49.95,100.4625)|C11.1(49.92,104.4)|3.938mm|0.900mm at(51.78,104.4)|
|U6.8 (63.475,96.695)|C17.1(66.2,96.775)|2.726mm|0.900mm at(67.1,95.225)|

These are straight pad-to-pad distances, **not** routed path inductance or proof that the nearest via has a direct trace. U5 output to C12 is about2.063mm. No universal distance pass limit is imposed. GND return measurement finds16stitching vias in strip and farthest sampled bottom-pour point7.8mm from a via. New PWM36.4mm trace has94.9% sampled GND coverage and largest uncovered component0.7mm; buffered PWM2.2mm has36.6% coverage and1.4mm uncovered. The latter is short, not a long microamp-net parallel run. No new heater/PWM-to-sensor proximity trigger fires; raw pair distances retained. The7top/3bottom ground pieces are not by themselves7/3isolated electrical nets: both layers/vias must be considered. DRC connectivity finds no opens.

Output39.4mm routed signal has94.1% sampled GND coverage,1.2mm uncovered component. J3.7 and stage ground share board GND and vias; no Kelvin isolation from heater current exists (known owner decision). Geometric coverage alone cannot establish the20mV ground-offset bring-up target; actual load/wiring measurement remains necessary.

## C11 edge assembly
MEASURED C11 center(50.4,104.4),0402body1x0.5mm, nearest outline y106.25: center1.85mm(0.073in), body-to-edge about1.60mm(0.063in). DOCUMENTED [JLC assembly terms](https://jlcpcb.com/help/article/terms-and-conditions-of-jlcpcb-assembly-service), DFM item3, require body-to-edge>=2.5mm(0.098in), not a center measurement. [JLC rail guidance](https://jlcpcb.com/help/article/how-to-add-edge-rails-fiducials-for-pcb-assembly-order) specifies minimum5mm(0.197in) rails. Thus an unpanelized interpretation is below published clearance by~0.9mm. Obtain the factory's panel/rail plan and acceptance; rails/fixture may resolve this without moving the circuit. Not evidence that a board with an approved rail process cannot be assembled.
