#pragma once

#include <cstdint>

void InitAuxDac();
void SetAuxDac(int channel, float voltage);
// Recompute the outputs once; boards without an aux thread call this from another thread
void UpdateAuxOut();
