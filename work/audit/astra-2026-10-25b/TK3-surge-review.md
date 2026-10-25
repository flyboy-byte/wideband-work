# TK3 — conditional surge result, not automotive qualification

Baseline:18b6cef,2026-10-25. **Answer: the R9 nominal overload is fixed; survival of an unspecified actual load dump is NOT established.** This is not a claim the board fails in normal use. Engine-bay qualification is not an owner requirement.

## Verified facts and calculations

- MEASURED `TK3-surge.log`: current checker passes, R9 0.475W,D5 0.378W at38.9V. It is a room-temperature arithmetic check, not a surge/thermal simulation.
- DOCUMENTED [Vishay CRCW-HP e3,20043,rev17-Mar-2026,p1](https://www.vishay.com/docs/20043/crcwhpe3.pdf): CRCW1206-HP P70=0.75W, maximum film155C; footnote3 requires assembled Rth<=110K/W. CALCULATED allowing R9 -1%: (38.9-17.1)^2/990=0.480W,64% of0.75W. At Rth110K/W the steady rise is52.8K; a70C ambient would give122.8C film. The actual assembly's thermal resistance is UNKNOWN. Continuous rating avoids needing a400ms pulse extrapolation, provided its thermal conditions hold.
- DOCUMENTED **MDD-authored** BZT52C2V0–BZT52C75,rev2025A6,p1–3, [supplier-hosted original family PDF](https://datasheet.lcsc.com/datasheet/pdf/61190d79e0f948958471ae8476bcd111.pdf): BZT52C18 is17.1–18.9V at5mA;500mW,150C junction. Typical RthetaJA305K/W uses5x5cm copper. Figure1 is **case**, not ambient, temperature:500mW through75C, then linear to zero at150C. CALCULATED D5 endpoint budget with990ohm:18.9*(38.9-18.9)/990=0.3818W, corresponding case ceiling150-75*(0.3818/0.5)=92.7C on that curve. At100C case only0.333W is allowed. Therefore blanket "76% of rating" is not a temperature-independent pass.
- INFERRED from MDD p2 typical transient curve: Zth near0.4s is approximately200K/W, so0.382W could raise the junction roughly76K from its pre-pulse condition. This is an approximate plot reading, not a maximum bound or a measurement on this board. Zener voltage is specified at5mA, while this event approaches20mA; dynamic resistance and temperature shift add uncertainty. No claim of guaranteed18.9V maximum at that current.
- DOCUMENTED [Littelfuse standard SMCJ datasheet,rev27-Feb-2025,p1–3](https://www.littelfuse.com/assetdocs/tvs-diodes-smcj-datasheet?assetguid=37388813-0d6d-4329-969b-1aa8b7614ac1): SMCJ24CA is38.9V at38.6A;1500W rating uses10/1000us, not400ms. Its specified pulse/copper/initial-temperature conditions matter. Thus38.9V is not a universal guaranteed cap for every load-dump source.

CALCULATED illustrative source, **not an owner requirement**:100V Thevenin source through2ohm would demand about(100-38.9)/2=30.55A,1188W while clamped. Holding that for400ms would be475J. This source is not equivalent to the rated10/1000us pulse. Real wave shape, source resistance, upstream suppression, wiring/fuse behavior and initial temperature must be specified before assigning survival. No destructive test is proposed on the owner's assembled board.

## Recommendation / minimum changes

Keep the HP R9 for the first prototype; do not silently substitute a generic250mW1206. Qualify the checker/doc wording as **conditional38.9V budget**, with D5 case-temperature and R9 thermal conditions. A guaranteed actual-load-dump claim needs an input envelope and TVS energy check first; changing only R9/D5 cannot repair an overstressed D1. If that defined envelope overloads D5, select an explicitly pulse/thermal-rated18V SOD-123 replacement and verify its pin geometry/stock; no unverified part number is nominated here. Normal bench operation does not require selecting a harsher automotive envelope.

## Research dead ends

Discarded HJC/Hongjiacheng BZT52 PDF (350mW) as the wrong manufacturer. A NextGen reseller's MDD-branded selection sheet was not used for exact-part limits. The retrieved MDD original is rev2025A6; do not confuse supplier page revision metadata with the PDF's own revision. Thermal evidence did not come from a search snippet.
