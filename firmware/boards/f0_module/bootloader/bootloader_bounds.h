#pragma once

#include <cstddef>
#include <cstdint>

// Whether a CAN DATA frame may write `length` bytes at `offset` from the start of the app partition.
// Accepts whole flash words only, at most one CAN payload (8 bytes), and only when the whole write lies inside the
// partition: the config page right after the app and the end of flash are never reachable from the updater.
// A zero-length frame writes nothing and stays accepted, as before.
inline bool IsAppWriteAllowed(uint32_t offset, size_t length, size_t appSize, size_t wordSize)
{
    if (length > 8)
    {
        return false;
    }

    if (offset % wordSize != 0 || length % wordSize != 0)
    {
        return false;
    }

    // Check the offset first so appSize - offset cannot wrap
    if (offset > appSize)
    {
        return false;
    }

    return length <= appSize - offset;
}
