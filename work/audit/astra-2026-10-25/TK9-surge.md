# TK9 op-amp rail transient energy

MEASURED BOM: R9=C4410,UNI-ROYAL1206W4F1001T5E; D5=C173425,MDD BZT52C18, **not** Diodes Inc's same-named product. Cached EasyEDA supplier metadata identifies these vendors. [LCSC exact D5](https://www.lcsc.com/product-detail/C173425.html) REPORTED18V/500mW; [exact R9](https://www.lcsc.com/product-detail/Chip-Resistor-Surface-Mount-UniOhm_1KR-1001-1_C4410.html) nominal1k/1206/0.25W supplier specification. Exact manufacturer's pulse/thermal qualification was not obtained; generic same-name parts cannot supply that evidence.

CALCULATED, assuming an ideal18V zener and neglecting op-amp current (conservatively overstates zener current, not resistor current):

| Protected input | R9 current | R9 power | D5 power | R9 energy400ms | D5 energy400ms |
| --- | --- | --- | --- | --- | --- |
|27V|9mA|81mW|162mW|0.0324J|0.0648J|
|38.9V|20.9mA|436.8mW|376.2mW|0.1747J|0.1505J|
|48V (old task envelope)|30mA|900mW|540mW|0.360J|0.216J|

At protected16V D5 is nominally off; R9 carries the op-amp quiescent/output current.1mA would dissipate1mW,5mA25mW. It is incorrect to use(16-18)/1k as a negative zener current. Actual continuous current depends on output load and clamp behavior, TK6/TK8.

RISK: the38.9V illustrative pulse demands1.75x R9's nominal continuous rating for400ms. That alone neither proves failure nor proves survival. Need the exact resistor's pulse-load curve at temperature/repetition, and exact MDD zener transient thermal/derating data. Zener tolerance/dynamic resistance affect clamp voltage; its500mW headline is conditional on thermal mounting. C16/C17 store only~1.64mJ at18V, negligible compared with400ms energy; they cannot absorb the pulse for the resistor.

The SMCJ24CA's~38.9V figure in project docs remains a conditional standard clamp value, not a measured load-dump waveform. A10/1000us TVS rating cannot establish survival for400ms: source impedance, peak voltage/current and repetition must be specified. Task's35-48V envelope belongs to an older TVS assumption; do not silently treat it as a current qualified requirement. Even if the analog clamp survives, upstream L78M05 has35V input absolute maximum (ST DS0425 p5); system surge survival is not established by this local calculation.

Smallest next step: qualify a documented pulse-rated1k resistor or obtain the current exact part's overload curve and actual protected waveform. No design file or rating was changed here.
