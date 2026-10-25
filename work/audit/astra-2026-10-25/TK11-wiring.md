# TK11 wiring cross-check

MEASURED from current PCB using pcbnew (not solely pack text):

| J3 terminal | Board net | wiring.md |
| --- | --- | --- |
|1|GND|matches power/heater ground|
|2|LSU_Ip|matches sensor1|
|3|LSU_Heater-|matches sensor3|
|4|LSU_Heater+|matches sensor4|
|5|AOUT_J|matches OUT|
|6|12V_RAW|matches supply|
|7|GND|matches output reference|
|8|LSU_Vm|matches sensor2|
|9|LSU_Rtrim|matches sensor5|
|10|LSU_Un|matches sensor6|
|11|CAN_H|matches H|
|12|CAN_L|matches L|

Module J2:1+3V3,2SWDIO,3nRESET,4SWCLK,5GND,6unconnectedSWO, all match. Inspected existing swd-pads.png: explicitly mirrored bottom view, pin labels match generator's net-derived mapping; it does not demonstrate a physical plug fitting. Owner's clone wiring maps2->SWDIO,4->SWCLK,5->GND,3->RST and leaves1/6disconnected. This is appropriate **if the actual clone's printed labels are correct**; its3.3V supply is not a target-reference input. No hardware pin labels verified.

DOCUMENTED [Tag-Connect TC2030-IDC-NL drawing revB](https://www.tag-connect.com/wp-content/uploads/bsk-pdf-manager/2019/12/TC2030-IDC-NL-Datasheet-Rev-B.pdf) sheet2 gives straight-through TAG1..6 to IDC1..6. Thus the owner's IDC-NL breakout mapping is now primary-datasheet-supported. Actual plug body and compressed spring reach through carrier remain untested;8x5.5mm aperture alone does not establish fit. Flashing the loose module first avoids this for initial programming; trim reflashing still needs access or a different fixture. No device flashed.

Remaining identity boundary: board pin numbers vs Molex moulded cavity numbers are explicitly INFERRED in wiring.md. Verify the actual housing and sensor plug before making the harness. Board-net agreement cannot settle mating-face mirroring of a connector not present here.

NOTE on protection claim: wiring.md's optional250-500mA signal-ground fuse is described as opening before receiver damage. A current rating alone does not establish that: exact fuse time-current/I²t, hot/cold resistance and receiver-ground withstand are missing. At2mA normal return a1ohm fuse adds2mV, small but not literally zero;2A fault at0.1ohm receiver-ground impedance creates0.4W there until clearing. Change the claim to an unqualified candidate requiring coordination, not assured protection. The shared ground itself is an existing owner decision, not re-raised as a new design defect.
