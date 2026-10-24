#include <gtest/gtest.h>

#include "heater_control.h"
#include "sampling.h"
#include "timer.h"

// F7 (work/docs/flashing-and-test-plan.md): the whole HeaterControllerBase::Update() path, called every
// HEATER_CONTROL_PERIOD like heater_thread.cpp, with the board's preheat and warmup times. The existing tests cover
// GetNextState(); these add the duty sent to the heater, standalone (no CAN) start-up, the voltage limits, a sensor
// disconnect in each state and the exact temperature boundaries. Expected values come from the rules written in
// heater_control.cpp and wideband_config.h: duty = (V_eff / V_supply)^2, V_eff capped at 12 V, supply below 3 V taken as
// 12 V, heater off at 23 V or more, preheat 2 V, ramp from 7 V at 0.4 V/s, closed loop above target - 30 C, stop after
// 0.5 s beyond target +- 100 C. LSU 4.9 target 780 C.

struct RecordingHeater final : public HeaterControllerBase
{
    RecordingHeater()
        : HeaterControllerBase(0, HEATER_PREHEAT_TIME, HEATER_WARMUP_TIMEOUT)
    {
        Configure(780, 300);
    }

    void SetDuty(float duty) const override { lastDuty = duty; }

    mutable float lastDuty = -1;
};

struct FakeSampler : public ISampler
{
    float temperature = 20;
    float supply = 13;   // what Sampler::GetInternalHeaterVoltage() reports on f0 after 5 s (0 before)

    float GetNernstDc() const override { return 0.45f; }
    float GetNernstAc() const override { return 0; }
    float GetPumpNominalCurrent() const override { return 0; }
    float GetInternalHeaterVoltage() const override { return supply; }
    float GetSensorTemperature() const override { return temperature; }
    float GetSensorInternalResistance() const override { return 300; }
};

class HeaterUpdate : public ::testing::Test
{
protected:
    void SetUp() override
    {
        Timer::setMockTime(0);
        // constructed after the clock is set, so Configure() resets the timers at t = 0
        dut = new RecordingHeater();
    }
    void TearDown() override { delete dut; }

    // Run the loop for `seconds`, one Update every HEATER_CONTROL_PERIOD ms (mock time is in microseconds)
    void Run(float seconds, HeaterAllow allow = HeaterAllow::Unknown)
    {
        int n = (int)(seconds * 1000 / HEATER_CONTROL_PERIOD + 0.5f);
        for (int i = 0; i < n; i++)
        {
            Timer::advanceMockTime(HEATER_CONTROL_PERIOD * 1000);
            dut->Update(sampler, allow);
        }
    }

    // Run until the heater enters `state`; returns the seconds it took (or -1 after maxSeconds)
    float RunUntil(HeaterState state, float maxSeconds)
    {
        for (float t = 0; t < maxSeconds; t += HEATER_CONTROL_PERIOD / 1000.0f)
        {
            Run(HEATER_CONTROL_PERIOD / 1000.0f);
            if (dut->GetHeaterState() == state)
                return t + HEATER_CONTROL_PERIOD / 1000.0f;
        }
        return -1;
    }

    // Drive a cold sensor through standalone start-up into closed loop at the target temperature
    void ReachClosedLoop()
    {
        Run(11);
        ASSERT_EQ(dut->GetHeaterState(), HeaterState::WarmupRamp);
        sampler.temperature = 780;
        Run(0.1f);
        ASSERT_EQ(dut->GetHeaterState(), HeaterState::ClosedLoop);
    }

    static float Duty(float volts, float supply) { return (volts / supply) * (volts / supply); }

    RecordingHeater* dut;
    FakeSampler sampler;
};

TEST_F(HeaterUpdate, PreheatIsTwoVoltsEffective)
{
    Run(1);
    EXPECT_EQ(dut->GetHeaterState(), HeaterState::Preheat);
    EXPECT_NEAR(dut->lastDuty, Duty(2, 13), 1e-6);
}

TEST_F(HeaterUpdate, LowOrMissingSupplyIsTakenAs12V)
{
    // Before the f0 sampler reports 13 V (first 5 s) the sensed supply is 0: the duty is computed for 12 V
    sampler.supply = 0;
    Run(1);
    EXPECT_EQ(dut->GetHeaterState(), HeaterState::Preheat);
    EXPECT_NEAR(dut->lastDuty, Duty(2, 12), 1e-6);
}

TEST_F(HeaterUpdate, StandaloneStartWithoutCan)
{
    // The f0 sampler reports 0 V for 5 s, then 13 V: the supply must look stable for 0.5 s, then preheat runs 5 s
    sampler.supply = 0;
    Run(5);
    EXPECT_EQ(dut->GetHeaterState(), HeaterState::Preheat);
    sampler.supply = 13;
    Run(5.4f);
    EXPECT_EQ(dut->GetHeaterState(), HeaterState::Preheat);
    Run(0.3f);
    EXPECT_EQ(dut->GetHeaterState(), HeaterState::WarmupRamp);
}

TEST_F(HeaterUpdate, SupplyAlready13VStartsTheRampAfterAbout5p5s)
{
    // Supply stable for 0.5 s, then 5 s of preheat
    float t = RunUntil(HeaterState::WarmupRamp, 20);
    EXPECT_GT(t, 5.5f);
    EXPECT_LT(t, 5.7f);
}

TEST_F(HeaterUpdate, RampsAt0p4VoltsPerSecondAndCapsAt12V)
{
    ASSERT_GT(RunUntil(HeaterState::WarmupRamp, 20), 0);
    // The ramp starts at 7 V and adds 0.4 V/s (0.02 V per 50 ms update, the first one in the same update)
    EXPECT_NEAR(dut->lastDuty, Duty(7.02f, 13), 1e-4);
    Run(5);
    EXPECT_NEAR(dut->lastDuty, Duty(7.02f + 0.4f * 5, 13), 1e-3);
    Run(30);
    EXPECT_NEAR(dut->lastDuty, Duty(12, 13), 1e-6);
}

TEST_F(HeaterUpdate, SensorThatNeverHeatsStopsAfterWarmupTimeout)
{
    ASSERT_GT(RunUntil(HeaterState::WarmupRamp, 20), 0);
    Run(HEATER_WARMUP_TIMEOUT - 1);
    EXPECT_EQ(dut->GetHeaterState(), HeaterState::WarmupRamp);
    Run(2);
    EXPECT_EQ(dut->GetHeaterState(), HeaterState::Stopped);
    EXPECT_EQ(dut->lastDuty, 0);
}

TEST_F(HeaterUpdate, OverVoltageTurnsTheHeaterOff)
{
    ReachClosedLoop();
    sampler.supply = 23;
    Run(0.1f);
    EXPECT_EQ(dut->lastDuty, 0);
    sampler.supply = 22.9f;
    Run(0.1f);
    EXPECT_GT(dut->lastDuty, 0);
}

TEST_F(HeaterUpdate, ClosedLoopEntryIsAboveTargetMinus30)
{
    Run(11);
    sampler.temperature = 750;   // exactly target - 30: not yet
    Run(0.1f);
    EXPECT_EQ(dut->GetHeaterState(), HeaterState::WarmupRamp);
    sampler.temperature = 750.5f;
    Run(0.1f);
    EXPECT_EQ(dut->GetHeaterState(), HeaterState::ClosedLoop);
}

TEST_F(HeaterUpdate, SensorDisconnectInClosedLoopStopsWithinHalfASecond)
{
    // A disconnected sensor reads as 0 C (ESR above 5000 ohm, sampling.cpp)
    ReachClosedLoop();
    sampler.temperature = 0;
    Run(0.45f);
    EXPECT_EQ(dut->GetHeaterState(), HeaterState::ClosedLoop);
    Run(0.15f);
    EXPECT_EQ(dut->GetHeaterState(), HeaterState::Stopped);
    EXPECT_EQ(dut->lastDuty, 0);
    // Stopped is final until reset, even when the sensor comes back
    sampler.temperature = 780;
    Run(5);
    EXPECT_EQ(dut->GetHeaterState(), HeaterState::Stopped);
    EXPECT_EQ(dut->lastDuty, 0);
}

TEST_F(HeaterUpdate, SensorDisconnectDuringPreheatTimesOutInWarmup)
{
    sampler.temperature = 0;
    Run(11 + HEATER_WARMUP_TIMEOUT + 1);
    EXPECT_EQ(dut->GetHeaterState(), HeaterState::Stopped);
    EXPECT_EQ(dut->lastDuty, 0);
}

TEST_F(HeaterUpdate, OverheatBoundary)
{
    ReachClosedLoop();
    sampler.temperature = 880;   // exactly target + 100: allowed indefinitely
    Run(2);
    EXPECT_EQ(dut->GetHeaterState(), HeaterState::ClosedLoop);
    sampler.temperature = 880.5f;
    Run(0.45f);
    EXPECT_EQ(dut->GetHeaterState(), HeaterState::ClosedLoop);
    Run(0.15f);
    EXPECT_EQ(dut->GetHeaterState(), HeaterState::Stopped);
}

TEST_F(HeaterUpdate, UnderheatBoundary)
{
    ReachClosedLoop();
    sampler.temperature = 680;   // exactly target - 100: allowed indefinitely
    Run(2);
    EXPECT_EQ(dut->GetHeaterState(), HeaterState::ClosedLoop);
    sampler.temperature = 679.5f;
    Run(0.6f);
    EXPECT_EQ(dut->GetHeaterState(), HeaterState::Stopped);
}

TEST_F(HeaterUpdate, CanSaysNoHeatHoldsPreheat)
{
    Run(20, HeaterAllow::NotAllowed);
    EXPECT_EQ(dut->GetHeaterState(), HeaterState::Preheat);
}
