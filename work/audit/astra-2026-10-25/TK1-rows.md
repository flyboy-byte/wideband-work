# Carrier row-by-row checks

Rotation corrections are checked against the cached measurement, not a JLC placement guarantee.

| BOM line | Refs | Value / LCSC / footprint matches board |
| --- | --- | --- |
| 1 | C1,C2,C3 | OK |
| 2 | C4,C5 | OK |
| 3 | C6 | OK |
| 4 | C7,C8,C9,C10,C16 | OK |
| 5 | C11,C12,C13,C14 | OK |
| 6 | C15 | OK |
| 7 | C17 | OK |
| 8 | D1 | OK |
| 9 | D2 | OK |
| 10 | D3,D4 | OK |
| 11 | D5 | OK |
| 12 | R1 | OK |
| 13 | R2 | OK |
| 14 | R3 | OK |
| 15 | R4,R5 | OK |
| 16 | R6 | OK |
| 17 | R7 | OK |
| 18 | R8 | OK |
| 19 | R9 | OK |
| 20 | R10 | OK |
| 21 | R11 | OK |
| 22 | U1 | OK |
| 23 | U2 | OK |
| 24 | U4 | OK |
| 25 | U5 | OK |
| 26 | U6 | OK |

| CPL ref | position residual mm | rotation matches measured correction | Top |
| --- | --- | --- | --- |
| C1 | 0.000000 | 0.000000 degrees | True |
| C2 | 0.000000 | 0.000000 degrees | True |
| C3 | 0.000000 | 0.000000 degrees | True |
| C4 | 0.000000 | 0.000000 degrees | True |
| C5 | 0.000000 | 0.000000 degrees | True |
| C6 | 0.000000 | 0.000000 degrees | True |
| C7 | 0.000000 | 0.000000 degrees | True |
| C8 | 0.000000 | 0.000000 degrees | True |
| C9 | 0.000000 | 0.000000 degrees | True |
| C10 | 0.000000 | 0.000000 degrees | True |
| C11 | 0.000000 | 0.000000 degrees | True |
| C12 | 0.000000 | 0.000000 degrees | True |
| C13 | 0.000000 | 0.000000 degrees | True |
| C14 | 0.000000 | 0.000000 degrees | True |
| C15 | 0.000000 | 0.000000 degrees | True |
| C16 | 0.000000 | 0.000000 degrees | True |
| C17 | 0.000000 | 0.000000 degrees | True |
| D1 | 0.000000 | 0.000000 degrees | True |
| D2 | 0.000000 | 0.000000 degrees | True |
| D3 | 0.000000 | 0.000000 degrees | True |
| D4 | 0.000000 | 0.000000 degrees | True |
| D5 | 0.000000 | 0.000000 degrees | True |
| R1 | 0.000000 | 0.000000 degrees | True |
| R2 | 0.000000 | 0.000000 degrees | True |
| R3 | 0.000000 | 0.000000 degrees | True |
| R4 | 0.000000 | 0.000000 degrees | True |
| R5 | 0.000000 | 0.000000 degrees | True |
| R6 | 0.000000 | 0.000000 degrees | True |
| R7 | 0.000000 | 0.000000 degrees | True |
| R8 | 0.000000 | 0.000000 degrees | True |
| R9 | 0.000000 | 0.000000 degrees | True |
| R10 | 0.000000 | 0.000000 degrees | True |
| R11 | 0.000000 | 0.000000 degrees | True |
| U1 | 0.000000 | 0.000000 degrees | True |
| U2 | 0.000000 | 0.000000 degrees | True |
| U4 | 0.000000 | 0.000000 degrees | True |
| U5 | 0.000000 | 0.000000 degrees | True |
| U6 | 0.000000 | 0.000000 degrees | True |

## Five high-risk parts: board pad nets and measured assembly transform

- D2: {"correction": 0, "cpl_rot": 270.0, "fit_mm": 0.504, "kicad_rot": 270.0, "lcsc": "C22452", "origin_offset_mm": 0.0, "paired_by": ["name"], "pins": 2, "polarized": true, "pos_shift_mm": [0.0, 0.0]}; pads 1:/LSU_Heater+, 2:12V_RAW
- U2: {"correction": 0, "cpl_rot": 270.0, "fit_mm": 0.01, "kicad_rot": 270.0, "lcsc": "C58069", "origin_offset_mm": 0.725, "paired_by": ["name"], "pins": 2, "polarized": false, "pos_shift_mm": [-0.0, -0.725]}; pads 1:/LSU_Heater+, 2:GND, 3:+5V
- U4: {"correction": 180, "cpl_rot": 0.0, "fit_mm": 0.008, "kicad_rot": 180.0, "lcsc": "C12519", "origin_offset_mm": 0.001, "paired_by": ["name", "number"], "pins": 5, "polarized": false, "pos_shift_mm": [0.0, 0.0]}; pads 1:GND, 2:/AOUT_PWM, 3:GND, 4:/AOUT_BUF, 5:/VREF3
- U5: {"correction": 180, "cpl_rot": 90.0, "fit_mm": 0.397, "kicad_rot": 270.0, "lcsc": "C38423", "origin_offset_mm": 0.099, "paired_by": ["name"], "pins": 3, "polarized": false, "pos_shift_mm": [0.0, 0.0]}; pads 1:+5V, 2:/VREF3, 3:GND
- U6: {"correction": 270, "cpl_rot": 270.0, "fit_mm": 0.125, "kicad_rot": 0.0, "lcsc": "C7934", "origin_offset_mm": 0.0, "paired_by": ["number"], "pins": 8, "polarized": false, "pos_shift_mm": [0.0, 0.0]}; pads 1:/AOUT_OA, 2:/AOUT_INN, 3:/AOUT_F2, 4:GND, 5:GND, 6:/U6B_FB, 7:/U6B_FB, 8:/VOP12
