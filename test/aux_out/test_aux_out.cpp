// Host tests for the 0-5 V analog output (docs/flashing-and-test-plan.md F3-F6), running the production auxout.cpp,
// pump_dac.cpp and can_helper.cpp with the real f0_module board config. Expected values come from the design
// (CLAUDE.md, work/docs/carrier.md), not from the code: full scale 3.000 V x 1.68 = 5.04 V; AFR 10 = 0 V ... 20 = 5 V;
// 5.0 V (20 AFR) while lambda is invalid (since 2026-10-24, outside review N1); test mode 1.00 / 2.50 / 4.00 V, 10 s each.

#include <gtest/gtest.h>

#include <cmath>
#include <limits>

#include "fakes.h"
#include "auxout.h"
#include "pump_dac.h"
#include "can_helper.h"

static constexpr float FullScale = 3.000f * 1.68f;   // 5.04 V
static constexpr int AuxTimer = 3, AuxChannel = 3;    // TIM3 CH4 (zero-based 3) on PB1
static constexpr int PumpChannel = 0;                 // TIM3 CH1, the pump DAC
static constexpr uint64_t TicksPerSecond = 10000;     // f0 chconf.h CH_CFG_ST_FREQUENCY

static float DutyFor(float volts) { return volts / FullScale; }
static const float InvalidDuty = 5.0f / FullScale;   // 5.0 V, the lean end
static float AfrToVolts(float afr) { return std::fmin(std::fmax((afr - 10.0f) / 10.0f * 5.0f, 0.0f), 5.0f); }

class AuxOut : public ::testing::Test
{
protected:
    void SetUp() override { fake::Reset(); }

    // Power-up order in main.cpp: pump DAC first (starts TIM3), then the aux output
    void Boot(bool sel2Low = false)
    {
        fake::sel2Low = sel2Low;
        InitPumpDac();
        InitAuxDac();
    }

    float AuxDuty() { return fake::LastDuty(AuxTimer, AuxChannel); }
};

// ---- F3: conversion, clamping, the shared timer
TEST_F(AuxOut, VoltsToDutyAgainstFullScale)
{
    Boot();
    const float cases[][2] = {{0.0f, 0.0f}, {1.0f, 1.0f}, {2.52f, 2.52f}, {5.0f, 5.0f}, {5.04f, 5.04f}};
    for (auto& c : cases)
    {
        SetAuxDac(0, c[0]);
        EXPECT_NEAR(AuxDuty(), DutyFor(c[1]), 1e-6) << c[0] << " V";
    }
}

TEST_F(AuxOut, OutOfRangeVoltsClampToTheEnds)
{
    Boot();
    SetAuxDac(0, -1.0f);
    EXPECT_EQ(AuxDuty(), 0.0f);
    SetAuxDac(0, 6.0f);
    EXPECT_EQ(AuxDuty(), 1.0f);
}

TEST_F(AuxOut, NanVoltsGoesToFullScale_Documented)
{
    // clampF(0, NaN, 1) returns 1. Nothing in the firmware feeds SetAuxDac a NaN today (an invalid lambda is replaced by
    // 0 V first, see below); recorded so a future caller knows
    Boot();
    SetAuxDac(0, std::numeric_limits<float>::quiet_NaN());
    EXPECT_EQ(AuxDuty(), 1.0f);
}

TEST_F(AuxOut, OnlyChannelZeroExists)
{
    Boot();
    int before = fake::DutyWrites(AuxTimer, AuxChannel);
    SetAuxDac(1, 2.0f);
    EXPECT_EQ(fake::DutyWrites(AuxTimer, AuxChannel), before);
}

TEST_F(AuxOut, SharesTim3WithoutTouchingThePump)
{
    Boot();
    // The pump DAC started TIM3 once (46.9 kHz = 48 MHz / 1024) and set the pump to zero current (half of VCC)
    ASSERT_EQ(fake::starts.size(), 1u);
    EXPECT_EQ(fake::starts[0].frequency, 48000000u);
    EXPECT_EQ(fake::starts[0].period, 1024u);
    float pump = fake::LastDuty(AuxTimer, PumpChannel);
    EXPECT_NEAR(pump, 0.5f, 1e-6);

    for (float v : {0.0f, 1.3f, 2.5f, 4.9f})
    {
        SetAuxDac(0, v);
        UpdateAuxOut();
    }
    // Only TIM3 channel index 3 was written by the aux output; no restart, no other timer, pump channel unchanged
    EXPECT_EQ(fake::starts.size(), 1u);
    for (auto& e : fake::events)
    {
        if (e.what == "duty" && e.channel != PumpChannel)
        {
            EXPECT_EQ(e.timer, AuxTimer);
            EXPECT_EQ(e.channel, AuxChannel);
        }
    }
    EXPECT_EQ(fake::LastDuty(AuxTimer, PumpChannel), pump);
}

TEST_F(AuxOut, InitDrivesZeroBeforeHandingPb1ToTheTimer)
{
    Boot();
    int duty = -1, pad = -1;
    for (size_t i = 0; i < fake::events.size(); i++)
    {
        auto& e = fake::events[i];
        if (duty < 0 && e.what == "duty" && e.channel == AuxChannel)
            duty = i;
        if (e.what == "padB" && e.channel == 1)
        {
            pad = i;
            EXPECT_EQ((uint32_t)e.value, PAL_MODE_ALTERNATE(1));   // PB1 = TIM3_CH4 is AF1
        }
    }
    ASSERT_GE(duty, 0);
    ASSERT_GE(pad, 0);
    EXPECT_LT(duty, pad);
    EXPECT_EQ(fake::events[duty].value, 0.0f);
}

// ---- F4: the curve and the validity policy
TEST_F(AuxOut, CurveFollowsAfr)
{
    Boot();
    for (float lambda : {0.70f, 0.80f, 0.90f, 1.00f, 1.10f, 1.20f, 1.30f})
    {
        fake::lambda = lambda;
        UpdateAuxOut();
        EXPECT_NEAR(AuxDuty(), DutyFor(AfrToVolts(14.7f * lambda)), 2e-4) << "lambda " << lambda;
    }
}

TEST_F(AuxOut, CurveClampsBelow10AndAbove20Afr)
{
    Boot();
    fake::lambda = 0.65f;   // 9.6 AFR
    UpdateAuxOut();
    EXPECT_EQ(AuxDuty(), 0.0f);
    fake::lambda = 1.5f;    // 22 AFR
    UpdateAuxOut();
    EXPECT_NEAR(AuxDuty(), DutyFor(5.0f), 1e-6);
}

TEST_F(AuxOut, InvalidWhileHeaterNotClosedLoop)
{
    Boot();
    fake::heaterClosedLoop = false;
    UpdateAuxOut();
    EXPECT_NEAR(AuxDuty(), InvalidDuty, 1e-6);
}

TEST_F(AuxOut, NernstWindowIsStrict)
{
    // Same test as the CAN Valid flag: 0.35 V < Nernst DC < 0.55 V (NERNST_TARGET 0.45 +- 0.1)
    Boot();
    const float valid = DutyFor(AfrToVolts(14.7f));
    const struct { float nernst; bool valid; } cases[] = {
        {0.45f, true}, {0.3501f, true}, {0.5499f, true}, {0.35f, false}, {0.55f, false}, {0.30f, false}, {0.80f, false}};
    for (auto& c : cases)
    {
        fake::nernstDc = c.nernst;
        UpdateAuxOut();
        EXPECT_NEAR(AuxDuty(), c.valid ? valid : InvalidDuty, 2e-4) << "Nernst " << c.nernst;
    }
}

TEST_F(AuxOut, NanLambdaIsInvalid)
{
    Boot();
    fake::lambda = std::numeric_limits<float>::quiet_NaN();
    UpdateAuxOut();
    EXPECT_NEAR(AuxDuty(), InvalidDuty, 1e-6);
}

TEST_F(AuxOut, InfiniteLambdaReadsFullScale_Documented)
{
    // +inf passes "lambda > 0.6" and clamps to the top of the curve: 5 V (20 AFR, lean). Recorded, not decided here
    Boot();
    fake::lambda = std::numeric_limits<float>::infinity();
    UpdateAuxOut();
    EXPECT_NEAR(AuxDuty(), DutyFor(5.0f), 1e-6);
}

// ---- F5: test mode (SEL_2 low at power-up)
TEST_F(AuxOut, TestModeStepsEvery10sIncludingAfterTheTickCounterWraps)
{
    Boot(true);
    const float levels[] = {1.00f, 2.50f, 4.00f};
    // 6.5536 s is where f0's 16-bit system time wraps; checks on both sides of it and of each 10 s step
    for (double s : {0.0, 5.0, 6.5535, 6.5537, 9.9999, 10.0, 13.2, 19.9999, 20.0, 29.9, 30.0, 40.0, 50.0, 3599.0, 86400.0})
    {
        fake::ticks = (uint64_t)(s * TicksPerSecond + 0.5);
        UpdateAuxOut();
        int step = (int)(fake::ticks / (10 * TicksPerSecond)) % 3;
        EXPECT_NEAR(AuxDuty(), DutyFor(levels[step]), 1e-6) << s << " s";
    }
}

TEST_F(AuxOut, TestModeIgnoresTheSensor)
{
    Boot(true);
    fake::heaterClosedLoop = false;
    fake::lambda = 1.2f;
    UpdateAuxOut();
    EXPECT_NEAR(AuxDuty(), DutyFor(1.00f), 1e-6);
}

TEST_F(AuxOut, StrapIsReadOnceAtPowerUp)
{
    Boot(false);
    fake::sel2Low = true;   // jumper closed after boot: no change
    UpdateAuxOut();
    EXPECT_NEAR(AuxDuty(), DutyFor(AfrToVolts(14.7f)), 2e-4);

    fake::Reset();
    Boot(true);
    fake::sel2Low = false;  // and the other way round
    UpdateAuxOut();
    EXPECT_NEAR(AuxDuty(), DutyFor(1.00f), 1e-6);
}

// ---- F6 (part): a CAN frame never waits for a mailbox on this board
TEST(CanTx, FrameIsDroppedNotWaitedFor)
{
    fake::Reset();
    fake::canResult = MSG_TIMEOUT;   // all mailboxes full, nobody acknowledging
    {
        CanTxMessage m(0x190, 8, false);
        m[0] = 1;
    }
    ASSERT_EQ(fake::canTimeouts.size(), 1u);
    EXPECT_EQ(fake::canTimeouts[0], TIME_IMMEDIATE);
}

// ---- F6: the production CAN TX thread loop (can.cpp) updates the output once per 10 ms cycle (WBO_TX_PERIOD_MS),
// whether or not anything on the bus takes the frames. A host scheduler, not real-time proof on the chip.
void CanTxThread(void*);
#include "can.h"

class CanTxLoop : public AuxOut
{
protected:
    void SetUp() override
    {
        AuxOut::SetUp();
        InitCan();   // reads the configuration the frames use; its threads are not started (fakes.cpp)
    }

    // Run the thread for `cycles` sleep windows; returns the output writes made by the loop (Boot's are not counted)
    int Run(int cycles)
    {
        int before = fake::DutyWrites(AuxTimer, AuxChannel);
        fake::loopCycles = cycles;
        try
        {
            CanTxThread(nullptr);
        }
        catch (fake::StopLoop&)
        {
        }
        return fake::DutyWrites(AuxTimer, AuxChannel) - before;
    }
};

static constexpr uint64_t CycleTicks = 100;   // 10 ms at 10 kHz

TEST_F(CanTxLoop, OneUpdatePerCycleWithFramesAcknowledged)
{
    Boot();
    EXPECT_EQ(Run(500), 500);
    EXPECT_EQ(fake::ticks, 500 * CycleTicks);
    EXPECT_EQ(fake::canTimeouts.size(), 2u * 500);   // StandardData + DiagData, one channel
}

TEST_F(CanTxLoop, NoAckOnTheBusStillUpdatesEveryCycle)
{
    // No other node: every mailbox stays full. 10 s of loop must be 1000 updates, not one per stalled frame
    Boot();
    fake::canResult = MSG_TIMEOUT;
    EXPECT_EQ(Run(1000), 1000);
    EXPECT_EQ(fake::ticks, 1000 * CycleTicks);
    for (auto t : fake::canTimeouts)
        ASSERT_EQ(t, TIME_IMMEDIATE);
    for (auto w : fake::sleepWindows)
        ASSERT_EQ(w, CycleTicks);
}

TEST_F(CanTxLoop, KeepsTheCadenceAcrossTheTickCounterWrap)
{
    // 16-bit system time wraps every 655.36 cycles: run through it twice
    Boot();
    EXPECT_EQ(Run(1400), 1400);
    EXPECT_EQ(fake::ticks, 1400 * CycleTicks);
}

TEST_F(CanTxLoop, OutputFollowsLambdaThroughTheThread)
{
    Boot();
    fake::lambda = 1.0f;
    Run(1);
    EXPECT_NEAR(AuxDuty(), DutyFor(AfrToVolts(14.7f)), 1e-3);
    fake::Reset();   // keep the boot state (statics), clear the records
    fake::lambda = 0.8f;
    Run(1);
    EXPECT_NEAR(AuxDuty(), DutyFor(AfrToVolts(0.8f * 14.7f)), 1e-3);
}

TEST_F(CanTxLoop, TestModeStepsThroughTheThreadWithTheBusDown)
{
    // F5 end to end: SEL_2 low at power-up, no CAN node, the real loop for 30 s gives 1.00, 2.50, 4.00 V
    Boot(true);
    fake::canResult = MSG_TIMEOUT;
    const float steps[] = {1.00f, 2.50f, 4.00f};
    for (float v : steps)
    {
        fake::sleepWindows.clear();
        Run(1000);
        EXPECT_NEAR(AuxDuty(), DutyFor(v), 1e-6) << v << " V";
    }
}
