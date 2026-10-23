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
