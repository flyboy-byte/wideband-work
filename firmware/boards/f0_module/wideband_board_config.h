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
// Output voltage at 100% duty, set by the carrier's reference buffer and op-amp gain
#define AUXOUT_FULL_SCALE_VOLTS (5.0f)
// Output while the sensor is warming up or lambda is invalid
#define AUXOUT_INVALID_VOLTS (0.0f)
