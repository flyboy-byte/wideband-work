# Parts research — <board name>

The maker's datasheet beats everything. Where the maker drawing and the EasyEDA footprint disagree,
use the maker drawing and note it. Every value has a source URL; mark scaled values **scaled**.

| Ref | Part | LCSC# | Class (Basic/Preferred/Extended) | Pinout | Land pattern | Keep-outs | Body / height | Temp | Current / ratings | 3D model checked | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Sensor choice (2026-10-23)
- Choice: Bosch LSU 4.9 (0 258 017 025). Owner plans to buy; wants performance and price weighed.
- Board support: upstream README says the module handles LSU 4.2, 4.9 or ADV (`upstream/hardware/README.md`).
- Price [REPORTED, unchecked, excl. shipping/duty, US shipping not confirmed]: about EUR 70-91 for a Bosch 4.9 at EU shops/eBay (llracing.eu EUR 91.33 incl. tax, EUR 71.92 excl.); GBP 69 in one UK listing. Cheap unbranded copies exist (about EUR 28) and sellers warn of shorter life. A 2019 rusEFI forum post said new 4.9 about $60 on Amazon (old).
- 4.2 vs 4.9 [REPORTED, enthusiast and maker pages]: 4.9 uses a pumping-current reference instead of a reference air cell, so claimed longer, steadier life; rusEFI forum says 4.2 needs periodic free-air calibration and has few OEM uses. 4.2 is cheaper to buy per one source.
- LSU ADV [UNKNOWN]: no price, accuracy or rusEFI support data found. Do not pick it.

## Wideband controller options surveyed (2026-10-23)
- rusEFI lambda-x2 (`rusefi-hardware/lambda-x2/readme.md`, cloned at ../rusefi-hardware): STM32F103 dual channel, LSU 4.9 and 4.2 (ADV in progress), CAN and analog out, Bluetooth or UART. "rev1 is known to work". Aux 0..5 V outputs are options not in the default BOM. Known hardware bugs in rev0/rev1 [DOCUMENTED in its readme]: ESR crosstalk between channels (remove listed resistors per sensor type), floating BOOT1/PB2 (jumper needed). Shop price: UNKNOWN (not found).
- wideband-F103 single channel: its readme says "RED ALERT, STATUS UNKNOWN... a bit abandoned" [DOCUMENTED]. Not a candidate.
- 14point7 Spartan 3 v2: closed, CAN + programmable analog, LSU 4.9/ADV, 10 ms response claimed [REPORTED, vendor/retailer]. Lite v2: about USD 82, programmable analog out and simulated narrowband, no CAN [REPORTED, retailer]. Full v2 price: UNKNOWN.
- AEM X-Series: closed, 0-5 V analog plus CAN, about 20 ms [REPORTED, one retailer review].
- Speeduino and Hondata FlashPro wideband input compatibility: UNKNOWN, not found in sources; check their docs.
- Conflict to resolve: a rusEFI wiki snippet says AEM X-Series CAN protocol is supported; mck1117 `firmware/can.cpp` only sends the rusEFI format. Check the dron0gus fork used by lambda-x2.
