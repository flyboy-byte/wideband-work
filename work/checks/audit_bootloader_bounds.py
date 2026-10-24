#!/usr/bin/env python3
"""Compile the actual CAN DATA guard with a recording Flash stub; never touches hardware.

Exit 1 means writes outside the application partition were accepted, or a valid write was refused. This tests
the guard only, not CAN hardware, flash programming, or complete bootloader execution.

History: written by Codex (f3cf90c) against the old guard (10 unsafe accepts of 48). Updated 2026-10-23 for the fix
(`bootloader_bounds.h`): the call site is still extracted from the real source and compiled with the real header.
"""
import os
from pathlib import Path
import subprocess
import tempfile

REPO = Path(__file__).resolve().parents[2]


def main():
    source = (REPO / 'firmware/boards/f0_module/bootloader/bootloader.cpp').read_text()
    start = source.index('if (!IsAppWriteAllowed(embeddedData')
    end = source.index('                break;', start)
    guard = source[start:end]
    # Fail visibly if the source shape changes; do not silently test a stale copy.
    assert 'Flash::Write(appFlashAddr + embeddedData' in guard
    code = r'''
#include <cstdint>
#include <cstdio>
#include "bootloader_bounds.h"
using flashdata_t = uint16_t;
constexpr uintptr_t appFlashAddr = 0x08001800;
constexpr unsigned appSize = 25 * 1024;    // wideband_layout.ld: 32k - 6k bootloader - 1k config
constexpr size_t appFlashSize = appSize;
static bool wrote;
static uintptr_t address;
static unsigned size;
struct Flash {
    static void Write(uintptr_t a, const uint8_t*, unsigned s) {
        wrote = true; address = a; size = s;
    }
};
void sendAck() {}
void sendNak() {}
void attempt(uint16_t embeddedData, unsigned length) {
    struct { unsigned DLC; uint8_t data8[8]; } frame = {length, {}};
''' + guard + r'''
}
int main() {
    unsigned bad = 0, tested = 0;
    for (unsigned off : {0u, 1u, 25592u, 25598u, 25600u, 26622u, 26624u, 65534u}) {
        for (unsigned len : {0u, 1u, 2u, 7u, 8u, 10u}) {
            wrote = false; attempt(off, len); ++tested;
            if (wrote && size && (size > 8 || address < appFlashAddr ||
                          address + size > appFlashAddr + appSize)) {
                std::printf("FAIL offset=%u length=%u accepted write at 0x%08lx\n",
                            off, len, static_cast<unsigned long>(address));
                ++bad;
            }
        }
    }
    // A guard that refuses everything would pass the loop above: valid writes must still go through
    struct { unsigned off, len; } good[] = {{0, 8}, {0, 2}, {25592, 8}, {25598, 2}};
    unsigned refused = 0;
    for (auto g : good) {
        wrote = false; attempt(g.off, g.len); ++tested;
        if (!wrote || address != appFlashAddr + g.off || size != g.len) {
            std::printf("FAIL offset=%u length=%u valid write refused\n", g.off, g.len);
            ++refused;
        }
    }
    std::printf("%u guard cases; %u unsafe accepted writes, %u valid writes refused (stub only)\n", tested, bad, refused);
    return (bad || refused) ? 1 : 0;
}
'''
    code = '#include <initializer_list>\n' + code
    with tempfile.TemporaryDirectory(prefix='wideband-boot-guard-') as tmp:
        cpp, binary = Path(tmp) / 'guard.cpp', Path(tmp) / 'guard'
        cpp.write_text(code)
        subprocess.run([os.environ.get('CXX', 'g++'), '-std=c++17', '-Wall', '-Wextra', '-Werror',
                        '-I', str(REPO / 'firmware/boards/f0_module/bootloader'), str(cpp), '-o', str(binary)],
                       check=True)
        return subprocess.run([str(binary)], check=False).returncode


if __name__ == '__main__':
    raise SystemExit(main())
