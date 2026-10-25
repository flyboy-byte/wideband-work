# TK3 boot/reset

MEASURED: TK3-boot.log passes both files. DOCUMENTED: app board.h:335 and bootloader/cfg/board.h:333 set PB1 pull-down. port.cpp:142-149 skips readSelPin(SEL1) under AUXOUT_SEL1_PWM_CHANNEL; SEL2 is still read. main.cpp:37-40 starts pump then auxiliary output. auxout.cpp:254-260 sets zero before handing PB1 to TIM3_CH4.

Primary sources read anew:
- [STM32F042 datasheet DocID025832 rev5](https://www.st.com/resource/en/datasheet/stm32f042k6.pdf) pp72-73: pull resistance25/40/55kohm. p75:8mA GPIO drive specified at VDD>=2.7V. MCU operating VDD maximum3.6V, not the checker's assumed3.4V.
- [Nexperia 74LVC1G125 rev17.1](https://assets.nexperia.com/documents/data-sheet/74LVC1G125.pdf) p5: VIL<=0.8V for2.7-3.6V supply; p1 specifies IOFF when unpowered, **not** a guaranteed output while supply rises through its unspecified region.

CALCULATED: with an old pull-up present, use MCU3.6V,25k minimum pull-up,R3=4747ohm (+1%): PB1=3.6*4747/(25000+4747)=0.5745V, margin0.2255V below0.8V. Current firmware has a pull-down, so no pull-up divider. Leakage, not literally0.000V, sets its DC residual. PWM current at3.6V,R3=4653ohm(-1%) is0.774mA; nominal3.3/4700=0.702mA. No strap or output-drive conflict found.

| State | Command and connector expectation | Evidence/limit |
| --- | --- | --- |
| Hardware reset, supplies settled | PB1 externally pulled low; nominal output approaches0V | R3, U4 enabled; not an exact-zero op-amp specification |
| Bootloader waiting/about0.8s | PB1 pull-down; nominal0V steady | boot board.h |
| CAN update/no valid app | same command indefinitely | bootloader owns pad, app never takes it |
| App init before PWM | pull-down; SetAuxDac(0,0) before alternate mode | app board.h,auxout.cpp |
| First ordinary app updates while warming | invalid command5V | TK4, deliberate transition |
| Warm reset from nonzero output | low command immediately; analog filter discharges over milliseconds | two330us RC sections retain charge; cannot claim instant0V |
| Supply ramp/brownout, receiver powered separately | UNKNOWN connector transient | LM2904 and buffer behavior below operating supply, clamp/backfeed and receiver pull-up need bench capture |

The checker verifies digital static conditions. It does not establish 'near0V in every case'; a receiver pull-up already has an accepted low-end error. Proposed bench test: capture J3-5 on cold start, warm reset from4V, interrupted CAN update and slow/rapid power cycling, with actual receiver attached. A multimeter can confirm the persistent bootloader level but cannot exclude a short transient; record that limitation rather than calling it passed.
