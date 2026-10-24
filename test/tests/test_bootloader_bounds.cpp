#include <gtest/gtest.h>

#include "f0_module/bootloader/bootloader_bounds.h"

// f0_module partition: 32k flash - 6k bootloader - 1k config page (boards/f0_module/wideband_layout.ld)
static constexpr size_t appSize = 25 * 1024;
// flashdata_t is uint16_t (shared/flash.h)
static constexpr size_t word = 2;

static bool allowed(uint32_t offset, size_t length)
{
    return IsAppWriteAllowed(offset, length, appSize, word);
}

TEST(BootloaderBounds, WholeImageInEightByteChunks)
{
    // The updater sends the 25600-byte image (app + CRC) as 3200 frames of 8 bytes
    for (uint32_t offset = 0; offset < appSize; offset += 8)
    {
        EXPECT_TRUE(allowed(offset, 8)) << offset;
    }
}

TEST(BootloaderBounds, ShortWritesInsideTheApp)
{
    EXPECT_TRUE(allowed(0, 2));
    EXPECT_TRUE(allowed(25592, 8));    // last full chunk, holds the CRC
    EXPECT_TRUE(allowed(25598, 2));    // last word
}

TEST(BootloaderBounds, ZeroLengthStaysAccepted)
{
    // Writes nothing; the protocol answered these with an ACK before and still does
    EXPECT_TRUE(allowed(0, 0));
    EXPECT_TRUE(allowed(appSize, 0));
}

TEST(BootloaderBounds, NeverReachesTheConfigPage)
{
    // The old guard accepted offsets up to 26 KiB: these all wrote into the config page at 0x08007C00
    EXPECT_FALSE(allowed(25600, 2));
    EXPECT_FALSE(allowed(25600, 8));
    EXPECT_FALSE(allowed(26622, 2));
    EXPECT_FALSE(allowed(26622, 8));
}

TEST(BootloaderBounds, NoWriteCrossesTheEnd)
{
    EXPECT_FALSE(allowed(25598, 4));
    EXPECT_FALSE(allowed(25598, 8));
    EXPECT_FALSE(allowed(25594, 8));
}

TEST(BootloaderBounds, FarOffsetsRejected)
{
    EXPECT_FALSE(allowed(26624, 2));
    EXPECT_FALSE(allowed(65534, 2));
    EXPECT_FALSE(allowed(65534, 0));
}

TEST(BootloaderBounds, MisalignedRejected)
{
    EXPECT_FALSE(allowed(1, 2));
    EXPECT_FALSE(allowed(0, 1));
    EXPECT_FALSE(allowed(0, 7));
    EXPECT_FALSE(allowed(25599, 1));
}

TEST(BootloaderBounds, OversizedPayloadRejected)
{
    EXPECT_FALSE(allowed(0, 10));
    EXPECT_FALSE(allowed(25592, 10));
}
