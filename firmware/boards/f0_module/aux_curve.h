#pragma once

#include "port.h"

// Compiled-in analog output curve for this board (no UART/TunerStudio to edit it): AFR 10.0 -> 0 V ... AFR 20.0 -> 5 V,
// linear (the 0 V = 10:1, 5 V = 20:1 standard). In a header so the host tests (test/aux_out) run the same code.
inline void SetCompiledAuxCurve(Configuration& config)
{
    for (int i = 0; i < 8; i++) {
        config.auxOutBins[0][i] = 10.0f + (20.0f - 10.0f) / 7 * i;
        config.auxOutValues[0][i] = 0.0f + (5.0f - 0.0f) / 7 * i;
    }
    config.auxOutputSource[0] = AuxOutputMode::Afr0;
}
