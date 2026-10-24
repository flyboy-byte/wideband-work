#include <gtest/gtest.h>

#include <string>
#include <vector>

#include "watchdog.h"
#include "wideband_config.h"

// D10 watchdog (firmware/watchdog.h): the register sequence and the timeout, on a fake IWDG that logs every access.
// Expected values come from the reference-manual sequence written in watchdog.h and the decision's limits (a hang must not
// hold the heater duty for over a second; the 50 ms heater loop must not trip it), not from the code.

struct Log
{
    std::vector<std::string> ops;
};

// One register: assignments and reads are logged in order
struct Reg
{
    Log* log;
    const char* name;
    std::vector<uint32_t> reads;   // values returned by successive reads (last one repeats)
    size_t nread = 0;

    Reg& operator=(uint32_t v)
    {
        log->ops.push_back(std::string(name) + "=" + std::to_string(v));
        return *this;
    }
    operator uint32_t()
    {
        log->ops.push_back(std::string(name) + "?");
        uint32_t v = reads.empty() ? 0 : reads[std::min(nread, reads.size() - 1)];
        nread++;
        return v;
    }
};

struct FakeIwdg
{
    Log log;
    Reg KR{&log, "KR", {}, 0}, PR{&log, "PR", {}, 0}, RLR{&log, "RLR", {}, 0}, SR{&log, "SR", {}, 0};
};

TEST(Watchdog, StartFollowsTheReferenceSequence)
{
    FakeIwdg w;
    watchdog::Start(w);
    std::vector<std::string> expect = {"KR=52428", "KR=21845", "PR=3", "RLR=625", "SR?", "KR=43690"};
    EXPECT_EQ(w.log.ops, expect);   // 0xCCCC start, 0x5555 unlock, values, wait for SR clear, 0xAAAA reload
}

TEST(Watchdog, StartWaitsUntilTheValuesHaveReachedTheWatchdog)
{
    FakeIwdg w;
    w.SR.reads = {3, 2, 0};   // PVU and RVU still set for two reads
    watchdog::Start(w);
    std::vector<std::string> expect = {"KR=52428", "KR=21845", "PR=3", "RLR=625", "SR?", "SR?", "SR?", "KR=43690"};
    EXPECT_EQ(w.log.ops, expect);
}

TEST(Watchdog, KickOnlyReloads)
{
    FakeIwdg w;
    watchdog::Kick(w);
    std::vector<std::string> expect = {"KR=43690"};
    EXPECT_EQ(w.log.ops, expect);
}

TEST(Watchdog, TimeoutCoversTheLsiRange)
{
    // LSI / 32, 625 counts: 400 ms at 50 kHz, 666 ms at 30 kHz, 500 ms at the typical 40 kHz
    EXPECT_EQ(watchdog::TimeoutMs(50000), 400u);
    EXPECT_EQ(watchdog::TimeoutMs(40000), 500u);
    EXPECT_EQ(watchdog::TimeoutMs(30000), 666u);
    EXPECT_EQ(watchdog::ShortestMs, 400u);
    EXPECT_EQ(watchdog::LongestMs, 666u);
}

TEST(Watchdog, HeaterLoopCanNotTripItAndAHangCanNotOutlastASecond)
{
    // The kick is once per HEATER_CONTROL_PERIOD (50 ms): even the fastest LSI leaves 8 periods
    EXPECT_GE(watchdog::ShortestMs, 8u * HEATER_CONTROL_PERIOD);
    EXPECT_LE(watchdog::LongestMs, 1000u);
}
