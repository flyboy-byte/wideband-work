#pragma once

// What the fakes record and the inputs the tests set (fakes.cpp). Reset with fake::Reset() before each test.

#include <cstdint>
#include <string>
#include <vector>

#include "hal.h"

namespace fake {

struct Event
{
    std::string what;   // "duty", "start", "pad"
    int timer;          // PWM: 1 or 3
    int channel;        // PWM channel, or GPIO pad
    float value;        // duty, or pad mode
};

extern std::vector<Event> events;
extern std::vector<PWMConfig> starts;   // configs passed to Pwm::Start, in order
extern uint64_t ticks;                  // 64-bit ticks since boot (10 kHz on f0)
extern bool sel2Low;
extern float nernstDc;
extern float lambda;
extern bool heaterClosedLoop;
extern std::vector<sysinterval_t> canTimeouts;
extern msg_t canResult;

// The CAN TX thread loop: chThdSleepUntilWindowed advances `ticks` to the window end, records the window, and throws
// StopLoop once `loopCycles` windows have passed, so the production while(1) can be run for a set number of cycles
struct StopLoop {};
extern int loopCycles;
extern std::vector<systime_t> sleepWindows;   // next - prev of each window (16-bit arithmetic, like the target)

void Reset();
// Last duty written to a PWM channel, or -1 if never written
float LastDuty(int timer, int channel);
int DutyWrites(int timer, int channel);

}
