# TK4 — no demonstrated minimum load; keep the accepted prototype trade-off

**Answers:** reliable load above13.6mA in every state? **No evidence establishes it.** Cheap no-layout swap worth making before this prototype? **No**, under the owner's accepted C1 fault scope. Do not interpret that choice as fault survival.

## Actual loads, not the hand-off's list

MEASURED board-net inventory in TK4-backfeed.log: +5V feeds TJA1051, REF3030, and module XC6206/REF3033. MCP6004,AD8628,MCU and LEDs load the3.3V/analog rails supplied through those devices. **LM2904 does not load +5V; U6.8 is VOP12.** Its approximately1mA cannot be counted as a guaranteed injection sink. Linear regulators pass load current, not a power-conversion ratio of3.3/5.

DOCUMENTED primary numerical anchors:

- [NXP TJA1051 rev9,p8 table7](https://www.nxp.com/docs/en/data-sheet/TJA1051.pdf): recessive5mA typical,10mA max; that table has no minimum. Quick-reference p2 lists2.5mA minimum, but even using that does not establish a13.6mA board floor. Silent/off variants must not be confused with the fitted /3 device; S is grounded here.
- [Microchip MCP6004 product data](https://www.microchip.com/en-us/product/MCP6004):100uA typical per amplifier, approximately0.4mA for four, before output loads. [ADI AD8628 revM,p4](https://www.analog.com/media/en/technical-documentation/data-sheets/AD8628_8629_8630.pdf):0.75mA typical at2.7V, not a minimum at the actual3.3V.
- [TI REF30 SBVS032K,p1,p9](https://www.ti.com/lit/ds/symlink/ref30.pdf):42uA typical per reference, plus output load. The newer REF30E is not the fitted part. [Torex ETR03005-009,p4](https://product.torexsemi.com/system/files/series/xc6206.pdf):XC6206 own1uA typical plus output load.
- [ST STM32F042,DocID025832 rev5,p55 table30](https://www.st.com/resource/en/datasheet/stm32f042k6.pdf): at48MHz/3.3V its illustrative flash-execution currents range from3.4mA (sleep,peripherals disabled) to20.7mA (run,peripherals enabled). These are **not the exact board firmware duty cycle**. Both app and bootloader configure48MHz (their cfg/mcuconf.h), but that does not guarantee continuous high-current execution. LED off intervals are explicit in firmware/main.cpp:60-90.

CALCULATED typical subtotal excluding MCU/IO/LED/ADC/buffer outputs:5+.4+.75+.084+.001=6.235mA. Adding those illustrative MCU states gives9.635–26.935mA **before extra loads**, not a predicted or guaranteed range for this board. Active operation may exceed13.6mA; reset, idle, boot and power-off cannot be declared safe from these typical numbers. Exact minimum/actual average is UNKNOWN without measurement.

## Rail rise and first failure

CALCULATED assuming0.6V diode and constant load, Vrail=12-.6-470*Iload:10mA gives6.7V;5mA gives9.05V; zero gives11.4V. These are illustrative equilibrium extrapolations, **not physical predictions after semiconductor limits are exceeded**. Capacitance controls the initial ramp, and regulator reverse paths/output-stage sink current change it.

DOCUMENTED TI REF30 operating input limit5.5V,absolute7V (p4); TJA1051 operating5.5V,absolute7V (p7–8); XC6206 operating6V,absolute7V (p1,p3). Therefore there is no basis to name a unique first failed component: several direct rail loads reach operating limits together and have7V absolute limits. MCU VDD is behind3.3V regulation, not immediately equal to the rising5V rail; once its regulator/reference is overstressed downstream behavior is UNKNOWN.

## No-layout choices and test proposal

CALCULATED R11=2.2k instead of470ohm reduces the held5V/12V-fault injection from13.62 to2.91mA, but does not clamp an unpowered rail. At5V into4.7k the required op-amp output rises from5.85 to7.69V, before supply/output headroom, increasing low-input-voltage dropout; stability and full-scale corners would need rerunning. Omitting D3 removes rail injection but also removes that protection path. Neither is a demonstrated drop-in cure. A dedicated shunt/isolation solution needs circuit/layout validation.

Recommendation: keep470ohm for the first prototype under C1, measure aggregate U2 output current in reset/boot/app/no-CAN/LED-off states, and retain the warning not to apply12V to J3-5. **A8 as written measures only the module branch as one option; that alone is not total+5V consumption**. A meter can measure benign supply loads, not prove fast fault survival. Do not perform uncontrolled12V backfeed testing with the owner's meter/iron setup; a bounded-current fixture plus voltage capture is a separate future qualification test.
