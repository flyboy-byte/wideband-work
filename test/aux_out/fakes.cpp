// Fakes for the analog-output host tests: the ChibiOS calls in shim/hal.h, the Pwm wrapper (firmware/pwm.h), and the
// sensor/heater/board functions auxout.cpp reads. The production code under test is compiled unchanged.

#include "fakes.h"

#include "pwm.h"
#include "port.h"
#include "sampling.h"
#include "heater_control.h"
#include "lambda_conversion.h"
#include "aux_curve.h"

PWMDriver PWMD1{1}, PWMD3{3};
FakeGpio fakeGpioA{'A'}, fakeGpioB{'B'};
CANDriver CAND1{1};

namespace fake {
std::vector<Event> events;
std::vector<PWMConfig> starts;
uint64_t ticks;
bool sel2Low;
float nernstDc;
float lambda;
bool heaterClosedLoop;
std::vector<sysinterval_t> canTimeouts;
msg_t canResult;

void Reset()
{
    events.clear();
    starts.clear();
    ticks = 0;
    sel2Low = false;
    nernstDc = 0.45f;
    lambda = 1.0f;
    heaterClosedLoop = true;
    canTimeouts.clear();
    canResult = MSG_OK;
}

float LastDuty(int timer, int channel)
{
    float d = -1;
    for (auto& e : events)
        if (e.what == "duty" && e.timer == timer && e.channel == channel)
            d = e.value;
    return d;
}

int DutyWrites(int timer, int channel)
{
    int n = 0;
    for (auto& e : events)
        n += e.what == "duty" && e.timer == timer && e.channel == channel;
    return n;
}
}

// ---- ChibiOS
systime_t chVTGetSystemTime() { return (systime_t)fake::ticks; }
systimestamp_t chVTGetTimeStamp() { return fake::ticks; }

void palSetPadMode(FakeGpio* port, int pad, uint32_t mode)
{
    fake::events.push_back({std::string("pad") + port->name, 0, pad, (float)mode});
}

msg_t canTransmitTimeout(CANDriver*, int, const CANTxFrame*, sysinterval_t timeout)
{
    fake::canTimeouts.push_back(timeout);
    return fake::canResult;
}

// ---- firmware/pwm.h, recorded instead of touching a timer
Pwm::Pwm(PWMDriver& driver) : m_driver(&driver) {}

void Pwm::Start(const PWMConfig& config)
{
    fake::starts.push_back(config);
    fake::events.push_back({"start", m_driver->timer, -1, 0});
}

void Pwm::SetDuty(int channel, float duty)
{
    m_dutyFloat[channel] = duty;
    fake::events.push_back({"duty", m_driver->timer, channel, duty});
}

float Pwm::GetLastDuty(int channel) { return m_dutyFloat[channel]; }

// ---- Sensor, heater and board functions auxout.cpp reads
struct FakeSampler : ISampler
{
    float GetNernstDc() const override { return fake::nernstDc; }
    float GetNernstAc() const override { return 0; }
    float GetPumpNominalCurrent() const override { return 0; }
    float GetInternalHeaterVoltage() const override { return 0; }
    float GetSensorTemperature() const override { return 780; }
    float GetSensorInternalResistance() const override { return 300; }
};
static FakeSampler sampler;
const ISampler& GetSampler(int) { return sampler; }

struct FakeHeater : IHeaterController
{
    void Update(const ISampler&, HeaterAllow) override {}
    bool IsRunningClosedLoop() const override { return fake::heaterClosedLoop; }
    float GetHeaterEffectiveVoltage() const override { return 0; }
    HeaterState GetHeaterState() const override { return HeaterState::ClosedLoop; }
    float GetTargetTemp() const override { return 780; }
};
static FakeHeater heater;
const IHeaterController& GetHeaterController(int) { return heater; }

float GetLambda(int) { return fake::lambda; }

// The board's compiled-in curve, from the same header port.cpp uses
Configuration* GetConfiguration()
{
    static Configuration config;
    SetCompiledAuxCurve(config);
    return &config;
}

bool IsSel2StrappedLow() { return fake::sel2Low; }
