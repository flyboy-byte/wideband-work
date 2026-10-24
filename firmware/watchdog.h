#pragma once

// Independent watchdog (IWDG), owner decision D10 (2026-10-23): a firmware hang must not leave the heater PWM at its last
// duty. The heater thread starts it and refreshes it every HEATER_CONTROL_PERIOD; if that loop stops running (a hang, a
// higher-priority thread spinning), the chip resets and the heater starts again from off. Faults already reset (F9).
// No RAM: registers only, so it fits the f0 build with 0 B free. Generic over the register block so the host tests drive
// the same sequence on a fake (test/tests/test_watchdog.cpp).
//
// Facts used (tags per AGENTS.md):
// - Sequence: KR = 0xCCCC starts the IWDG and the LSI, 0x5555 unlocks PR/RLR, SR's PVU/RVU bits clear when the values
//   have reached the LSI domain, 0xAAAA reloads the counter [FROM MEMORY, RM0091 IWDG; same on F1].
// - Once started it stops only on a reset, and NVIC_SystemReset counts, so the CAN bootloader (entered by a software
//   reset) runs with it off [REPORTED, ST IWDG training deck]. That holds while the option byte WDG_SW is at its factory
//   default (software watchdog) [FROM MEMORY].
// - LSI 30-50 kHz on the F042 [FROM MEMORY, datasheet]: hence the timeout range below.

#include <cstdint>

namespace watchdog
{

constexpr uint32_t KeyStart = 0xCCCC;
constexpr uint32_t KeyUnlock = 0x5555;
constexpr uint32_t KeyReload = 0xAAAA;

constexpr uint32_t Prescaler = 3;     // PR = 3: LSI / 32
constexpr uint32_t Reload = 625;      // RLR, 12 bits

constexpr uint32_t Divider = 4u << Prescaler;
constexpr uint32_t TimeoutMs(uint32_t lsiHz) { return Divider * Reload * 1000u / lsiHz; }

constexpr uint32_t LsiMinHz = 30000, LsiMaxHz = 50000;
constexpr uint32_t ShortestMs = TimeoutMs(LsiMaxHz);   // 400 ms
constexpr uint32_t LongestMs = TimeoutMs(LsiMinHz);    // 666 ms

static_assert(Reload <= 0xFFF, "RLR is 12 bits");
static_assert(Prescaler <= 6, "PR is 0-6");
// Room for a late heater loop (a flash page erase for the CAN set-index message stalls the CPU for tens of ms), but the
// heater can't sit at a stale duty for long
static_assert(ShortestMs >= 300, "timeout too close to the heater loop period");
static_assert(LongestMs <= 1000, "a hang would hold the heater duty for over a second");

template <typename Iwdg>
void Start(Iwdg& iwdg)
{
    iwdg.KR = KeyStart;
    iwdg.KR = KeyUnlock;
    iwdg.PR = Prescaler;
    iwdg.RLR = Reload;
    // Wait until both values have reached the watchdog. If the LSI never runs this never ends, and the IWDG, already
    // started with its reset values (about 0.4 s), resets the chip
    while (iwdg.SR != 0)
    {
    }
    iwdg.KR = KeyReload;
}

template <typename Iwdg>
void Kick(Iwdg& iwdg)
{
    iwdg.KR = KeyReload;
}

}
