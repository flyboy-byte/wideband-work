#include "pwm.h"
#include "dac.h"
#include "lambda_conversion.h"
#include "port.h"
#include "io_pins.h"
#include "pump_dac.h"
#include "sampling.h"
#include "heater_control.h"

#include "wideband_config.h"

#include "max3185x.h"

#include "hal.h"

#include <rusefi/math.h>
#include <rusefi/interpolation.h>

#ifdef AUXOUT_DAC_PWM_DEVICE

#ifndef AUXOUT_DAC_PWM_OUTPUT_MODE
#define AUXOUT_DAC_PWM_OUTPUT_MODE PWM_OUTPUT_ACTIVE_HIGH
#endif
#ifndef AUXOUT_DAC_PWM_NC_OUTPUT_MODE
#define AUXOUT_DAC_PWM_NC_OUTPUT_MODE PWM_OUTPUT_ACTIVE_LOW
#endif

// Rev2 low pass filter cut frequency is about 21Hz (sic!)
// 48Mhz / (2 ^ 12) ~= 12 KHz
// 64mhz / (2 ^ 12) ~= 16 KHz
static PWMConfig auxPwmConfig = {
    .frequency = STM32_SYSCLK,
    .period = 1 << 12,
    .callback = nullptr,
    .channels = {[0] = {0, nullptr}, [1] = {0, nullptr}, [2] = {0, nullptr}, [3] = {0, nullptr}},
    .cr2 = 0,
#if STM32_PWM_USE_ADVANCED
    .bdtr = 0,
#endif
    .dier = 0};

static void auxDacFillPwmConfig(void)
{
    auxPwmConfig.channels[AUXOUT_DAC_PWM_CHANNEL_0].mode = AUXOUT_DAC_PWM_OUTPUT_MODE;
    auxPwmConfig.channels[AUXOUT_DAC_PWM_CHANNEL_1].mode = AUXOUT_DAC_PWM_OUTPUT_MODE;
#ifdef AUXOUT_DAC_PWM_CHANNEL_0_NC
    auxPwmConfig.channels[AUXOUT_DAC_PWM_CHANNEL_0_NC].mode = AUXOUT_DAC_PWM_NC_OUTPUT_MODE;
#endif
#ifdef AUXOUT_DAC_PWM_CHANNEL_1_NC
    auxPwmConfig.channels[AUXOUT_DAC_PWM_CHANNEL_1_NC].mode = AUXOUT_DAC_PWM_NC_OUTPUT_MODE;
#endif
}

static Pwm auxDac(AUXOUT_DAC_PWM_DEVICE);

static const uint8_t auxOutPwmCh[AFR_CHANNELS] = {
    AUXOUT_DAC_PWM_CHANNEL_0,
#if (AFR_CHANNELS > 1)
    AUXOUT_DAC_PWM_CHANNEL_1,
#endif
};

static const int8_t auxOutPwmChN[AFR_CHANNELS] = {
#ifdef AUXOUT_DAC_PWM_CHANNEL_0_NC
    AUXOUT_DAC_PWM_CHANNEL_0_NC,
#else
    -1,
#endif
#if (AFR_CHANNELS > 1)
#ifdef AUXOUT_DAC_PWM_CHANNEL_1_NC
    AUXOUT_DAC_PWM_CHANNEL_1_NC,
#else
    -1,
#endif
#endif
};

void SetAuxDac(int channel, float voltage)
{
    voltage = voltage / AUXOUT_GAIN;
    auto duty = voltage / VCC_VOLTS;
    duty = clampF(0, duty, 1);

    auxDac.SetDuty(auxOutPwmCh[channel], duty);
    // Ripple cancelation channel
    if (auxOutPwmChN[channel >= 0])
    {
        auxDac.SetDuty(auxOutPwmChN[channel], duty);
    }
}

#endif

#ifdef AUXOUT_DAC_DEVICE

static DACConfig auxDacConfig = {.init = 2047U, .datamode = DAC_DHRM_12BIT_RIGHT, .cr = 0};

static Dac auxDac(AUXOUT_DAC_DEVICE);

static const uint8_t auxOutDacCh[] = {
    AUXOUT_DAC_CHANNEL_0,
#if (AFR_CHANNELS > 1)
    AUXOUT_DAC_CHANNEL_1,
#endif
};

void SetAuxDac(int channel, float voltage)
{
    voltage = voltage / AUXOUT_GAIN;

    auxDac.SetVoltage(auxOutDacCh[channel], voltage);
}

#endif /* AUXOUT_DAC_DEVICE */

#ifdef AUXOUT_SEL1_PWM_CHANNEL

// No timer of its own: the output is a spare channel on the pump DAC timer (TIM3 CH4 on PB1)
void SetAuxDac(int channel, float voltage)
{
    if (channel != 0)
    {
        return;
    }

    voltage = (voltage - AUXOUT_TRIM_OFFSET_VOLTS) / AUXOUT_TRIM_GAIN;

    auto duty = voltage / AUXOUT_FULL_SCALE_VOLTS;
    duty = clampF(0, duty, 1);

    SetPumpTimerDuty(AUXOUT_SEL1_PWM_CHANNEL, duty);
}

#endif /* AUXOUT_SEL1_PWM_CHANNEL */

#if (defined(AUXOUT_DAC_PWM_DEVICE) || defined(AUXOUT_DAC_DEVICE) || defined(AUXOUT_SEL1_PWM_CHANNEL))

static float AuxGetInputSignal(AuxOutputMode sel)
{
    switch (sel)
    {
    case AuxOutputMode::Afr0: return 14.7f * GetLambda(0);
    case AuxOutputMode::Afr1: return 14.7f * GetLambda(1);
    case AuxOutputMode::Lambda0: return GetLambda(0);
    case AuxOutputMode::Lambda1: return GetLambda(1);
#if HAL_USE_SPI
    case AuxOutputMode::Egt0: return getEgtDrivers()[0].temperature;
    case AuxOutputMode::Egt1: return getEgtDrivers()[1].temperature;
#endif
    default: return 0;
    }

    return 0;
}

static const Configuration* auxCfg;

#ifdef AUXOUT_INVALID_VOLTS
// Same test as the CAN frame's Valid flag (can.cpp)
static bool IsLambdaValid(int ch)
{
    auto nernstDc = GetSampler(ch).GetNernstDc();
    bool lambdaValid = nernstDc > (NERNST_TARGET - 0.1f) && nernstDc < (NERNST_TARGET + 0.1f) && GetLambda(ch) > 0.6f;

    return lambdaValid && GetHeaterController(ch).IsRunningClosedLoop();
}
#endif

#ifdef AUXOUT_TEST_MODE_ON_SEL2_LOW
// boards/f0_module/port.cpp
bool IsSel2StrappedLow();

static bool auxTestMode;
#endif

void UpdateAuxOut()
{
    if (!auxCfg)
    {
        return;
    }

#ifdef AUXOUT_TEST_MODE_ON_SEL2_LOW
    if (auxTestMode)
    {
        // Bench test A1: fixed voltages to read with a multimeter
        static const float levels[] = {1.00f, 2.50f, 4.00f};
        auto step = (TIME_I2MS(chVTGetSystemTime()) / AUXOUT_TEST_STEP_MS) % 3;
        SetAuxDac(0, levels[step]);
        return;
    }
#endif

    for (int ch = 0; ch < AFR_CHANNELS; ch++)
    {
        float input = AuxGetInputSignal(auxCfg->auxOutputSource[ch]);
        float voltage = interpolate2d(input, auxCfg->auxOutBins[ch], auxCfg->auxOutValues[ch]);

#ifdef AUXOUT_INVALID_VOLTS
        if (!IsLambdaValid(ch))
        {
            voltage = AUXOUT_INVALID_VOLTS;
        }
#endif

        SetAuxDac(ch, voltage);
    }
}

#ifndef AUXOUT_SEL1_PWM_CHANNEL
/* TODO: merge with some other communication thread? */
static THD_WORKING_AREA(waAuxOutThread, 256);
void AuxOutThread(void*)
{
    chRegSetThreadName("Aux out");

    while (1)
    {
        UpdateAuxOut();

        chThdSleepMilliseconds(10);
    }
}
#endif

void InitAuxDac()
{
    auxCfg = GetConfiguration();

#if defined(AUXOUT_DAC_PWM_DEVICE)
    auxDacFillPwmConfig();
    auxDac.Start(auxPwmConfig);

    SetAuxDac(0, 0.0);
    SetAuxDac(1, 0.0);
#endif
#if defined(AUXOUT_DAC_DEVICE)
    auxDac.Start(auxDacConfig);

    SetAuxDac(0, 0.0);
#endif

#if defined(AUXOUT_SEL1_PWM_CHANNEL)
    // The pump DAC has started TIM3 (InitPumpDac runs first); hand PB1 to TIM3_CH4 (AF1).
    // No RAM for another thread here: the CAN TX thread calls UpdateAuxOut().
    SetAuxDac(0, 0.0);
    palSetPadMode(GPIOB, 1, PAL_MODE_ALTERNATE(1));
#ifdef AUXOUT_TEST_MODE_ON_SEL2_LOW
    auxTestMode = IsSel2StrappedLow();
#endif
#else
    chThdCreateStatic(waAuxOutThread, sizeof(waAuxOutThread), NORMALPRIO, AuxOutThread, nullptr);
#endif
}

#else /* (AUXOUT_DAC_PWM_DEVICE || AUXOUT_DAC_DEVICE || AUXOUT_SEL1_PWM_CHANNEL) */

void InitAuxDac() {}
void UpdateAuxOut() {}

#endif
