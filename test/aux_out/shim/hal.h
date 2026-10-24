#pragma once

// Fake ChibiOS HAL for the analog-output host tests (test/aux_out): only what auxout.cpp, pump_dac.cpp and can_helper.cpp
// use. Calls land in fakes.cpp, which records them. Not a model of the STM32.

#include <cstdint>
#include <cstddef>

#ifndef FALSE
#define FALSE 0
#define TRUE 1
#endif

#define HAL_USE_DAC FALSE
#define HAL_USE_SPI FALSE

// ---- System time, as configured for f0_module: CH_CFG_ST_RESOLUTION and CH_CFG_ST_FREQUENCY come from its chconf.h
#include "chconf.h"
#if CH_CFG_ST_RESOLUTION == 16
typedef uint16_t systime_t;
#elif CH_CFG_ST_RESOLUTION == 32
typedef uint32_t systime_t;
#else
typedef uint64_t systime_t;
#endif
typedef uint64_t systimestamp_t;
typedef uint32_t sysinterval_t;
typedef uint64_t time_conv_t;
typedef uint32_t time_msecs_t;
// Same arithmetic as ChibiOS os/rt/include/chtime.h
#define TIME_I2MS(interval)                                                                                           \
    (time_msecs_t)((((time_conv_t)(interval) * (time_conv_t)1000) + (time_conv_t)CH_CFG_ST_FREQUENCY - (time_conv_t)1) / \
                   (time_conv_t)CH_CFG_ST_FREQUENCY)
#define TIME_MS2I(msecs)                                                                                              \
    ((sysinterval_t)((((time_conv_t)(msecs) * (time_conv_t)CH_CFG_ST_FREQUENCY) + (time_conv_t)999) / (time_conv_t)1000))
#define TIME_IMMEDIATE ((sysinterval_t)0)
#define TIME_INFINITE ((sysinterval_t)-1)

systime_t chVTGetSystemTime();       // the 16-bit tick counter: wraps like the real one
systimestamp_t chVTGetTimeStamp();   // 64-bit ticks since boot

// ---- PWM (the fields pump_dac.cpp's initializer fills)
struct PWMDriver
{
    int timer;
};
extern PWMDriver PWMD1, PWMD3;
typedef void (*pwmcallback_t)(PWMDriver*);
struct PWMChannelConfig
{
    uint32_t mode;
    pwmcallback_t callback;
};
struct PWMConfig
{
    uint32_t frequency;
    uint32_t period;
    pwmcallback_t callback;
    PWMChannelConfig channels[4];
    uint32_t cr2;
    uint32_t dier;
};
#define STM32_PWM_USE_ADVANCED FALSE
#define STM32_SYSCLK 48000000
#define PWM_OUTPUT_ACTIVE_HIGH 0x01
#define PWM_OUTPUT_ACTIVE_LOW 0x02
#define PWM_COMPLEMENTARY_OUTPUT_ACTIVE_LOW 0x20

// ---- GPIO
struct FakeGpio
{
    char name;
};
extern FakeGpio fakeGpioA, fakeGpioB;
#define GPIOA (&fakeGpioA)
#define GPIOB (&fakeGpioB)
#define PAL_MODE_ALTERNATE(n) (0x1000u | (n))
void palSetPadMode(FakeGpio* port, int pad, uint32_t mode);

// ---- CAN (bxCAN frame layout reduced to the fields can_helper.cpp touches)
typedef int32_t msg_t;
#define MSG_OK ((msg_t)0)
#define MSG_TIMEOUT ((msg_t)-1)
#define CAN_RTR_DATA 0
#define CAN_IDE_STD 0
#define CAN_IDE_EXT 1
#define CAN_ANY_MAILBOX 0
struct CANDriver
{
    int unit;
};
extern CANDriver CAND1;
struct CANTxFrame
{
    uint8_t DLC;
    uint8_t RTR;
    uint8_t IDE;
    uint32_t SID;
    uint32_t EID;
    uint8_t data8[8];
};
msg_t canTransmitTimeout(CANDriver* canp, int mailbox, const CANTxFrame* ctfp, sysinterval_t timeout);
struct CANRxFrame
{
    uint8_t DLC;
    uint8_t RTR;
    uint8_t IDE;
    uint32_t SID;
    uint32_t EID;
    uint8_t data8[8];
};
struct CANConfig
{
    int unused;
};
msg_t canReceiveTimeout(CANDriver* canp, int mailbox, CANRxFrame* crfp, sysinterval_t timeout);
void canStart(CANDriver* canp, const CANConfig* config);
const CANConfig& GetCanConfig();   // port_shared.h declares it only when WB_PROD

// ---- Threads (what can.cpp uses; the CAN TX loop runs in the test's own thread, see fakes.h StopLoop)
#define NORMALPRIO 128
#define THD_WORKING_AREA(s, n) char s[n]
typedef void (*tfunc_t)(void*);
void chRegSetThreadName(const char* name);
void* chThdCreateStatic(void* wsp, size_t size, int prio, tfunc_t pf, void* arg);
void chThdSleep(sysinterval_t time);
// Same arithmetic as ChibiOS chtime.h: wraps at the systime_t width
inline systime_t chTimeAddX(systime_t systime, sysinterval_t interval) { return (systime_t)(systime + interval); }
systime_t chThdSleepUntilWindowed(systime_t prev, systime_t next);
void NVIC_SystemReset();
