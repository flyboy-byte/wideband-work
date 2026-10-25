#pragma once

// Fundamental board constants
#define VCC_VOLTS (3.3f)
#define HALF_VCC (VCC_VOLTS / 2)
#define ADC_MAX_COUNT (4095)
#define ADC_OVERSAMPLE 24

// *******************************
//    Nernst voltage & ESR sense
// *******************************
#define NERNST_INPUT_GAIN (2.7f)

#define AFR_CHANNELS 1

// *******************************
//    Nernst voltage & ESR sense
// *******************************
#define VM_RESISTOR_VALUE (10)

// *******************************
//    Analog output (wideband-work carrier)
// *******************************
// Module pad SEL_1 (PB1) carries a PWM on TIM3 channel 4, sharing the pump DAC timer.
// The carrier filters it and scales it to 0-5 V. SEL_1 is no longer a CAN index strap.
#define AUXOUT_SEL1_PWM_CHANNEL 3
// Output voltage at 100% duty: REF3030 (3.0 V) buffer, op-amp gain 1 + 68k/100k (work/docs/carrier.md)
#define AUXOUT_FULL_SCALE_VOLTS (3.0f * (1.0f + 68.0f / 100.0f))
// Output while the sensor is warming up or lambda is invalid: 5.0 V = 20 AFR, the lean end. A closed-loop ECU that
// misses the fault then adds fuel (runs rich) rather than pulling it, and a log shows an off-scale value. 0 V read as
// 10 AFR, a believable rich reading, and into a pull-up input it floors at 0.6-1 V = 11-12 AFR (outside review N1,
// 2026-10-24; decided by Claude on the owner's delegation)
#define AUXOUT_INVALID_VOLTS (5.0f)
// Per-board trim from bring-up test A1 (measured = gain * wanted + offset, so we send (wanted - offset) / gain).
// Overridable at build time for one board, e.g. make BOARD=f0_module UDEFS='-DAUXOUT_TRIM_GAIN=1.012f'
#ifndef AUXOUT_TRIM_GAIN
#define AUXOUT_TRIM_GAIN (1.0f)
#endif
#ifndef AUXOUT_TRIM_OFFSET_VOLTS
#define AUXOUT_TRIM_OFFSET_VOLTS (0.0f)
#endif
// SEL_2 held low at power-up: output steps through these, AUXOUT_TEST_STEP_MS each, instead of the AFR
#define AUXOUT_TEST_MODE_ON_SEL2_LOW
#define AUXOUT_TEST_STEP_MS 10000

// Independent watchdog, refreshed by the heater loop: a hang resets the chip with the heater off (firmware/watchdog.h,
// owner decision D10)
#define WB_WATCHDOG
