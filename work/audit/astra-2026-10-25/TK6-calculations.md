# TK6 independent analog calculations

DOCUMENTED board topology: R4/R5=3300ohm,C13/C14=100nF,R6=68k,R7=100k,C15=1nF,R8=330,R11=470; DC feedback from connector. Measurements use TI SNOM268 typical macromodel and generic diode parameters, not process corners.

CALCULATED unloaded gain=1+68/100=1.68;3.000V reference gives5.040V maximum PWM amplitude. A requested5V uses duty5/5.04=0.9920635 before timer quantization.1% resistor extremes give gain1.666535..1.693737, or-0.8015%..+0.8177% relative gain. Two-point calibration can correct linear gain/offset, not clipping or low-end current-sink saturation.

CALCULATED: the unbuffered equal-component RC ladder has H(s)=1/[1+3sRC+(sRC)^2], **not** two independently buffered single poles. RC=330us;slow pole time constant864us. At46,875Hz, |H|=0.00010582.50%-duty3V PWM fundamental amplitude=6/pi V; after gain1.68, its output ripple p-p contribution=0.6791mV. Higher harmonics slightly modify waveform/total ripple; this is a first-harmonic estimate and excludes buffer supply noise, PCB coupling and aliasing. Nominal filter1% step settling is a few ms.

DOCUMENTED primary correction: TI [SLOS068AB](https://www.ti.com/lit/ds/symlink/lm2904.pdf) section5.8 p11 gives plain LM2904 **3mV typical,7mV maximum** offset at25C;10mV over its rated temperature range. `docs/carrier.md:134,143` treats3mV as the bound. CALCULATED output contribution from offset alone is±11.76mV at25C, not±5.04mV.7mV difference in input offset between parts cannot be inferred from the typical macromodel. Bias current is also20nA typical/250nA maximum at25C and500nA over temperature; finite source/feedback impedances introduce another calibratable offset. The±7mV specification alone is enough to invalidate a3mV worst-case budget, without assigning correlated current extrema.

Headroom: 1mA supply+load current costs1V acrossR9. It can cost several volts with clamp conduction; the actual rail must come from the simulated or measured current, not simply battery minus diode drop. Supply and clamp diode process/temperature corners remain unqualified.
