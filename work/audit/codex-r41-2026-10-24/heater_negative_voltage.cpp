// Independent reproduction against unmodified production heater/PID/timer code.
#include "heater_control.h"
#include "sampling.h"
#include "status.h"
#include <algorithm>
#include <cstdio>

void SetStatus(int, wbo::Status) {}
float GetRemoteBatteryVoltage() { return 13; }

struct Sample : ISampler {
    float esr=300, temp=780;
    float GetNernstDc() const override { return .45f; }
    float GetNernstAc() const override { return 0; }
    float GetPumpNominalCurrent() const override { return 0; }
    float GetInternalHeaterVoltage() const override { return 13; }
    float GetSensorTemperature() const override { return temp; }
    float GetSensorInternalResistance() const override { return esr; }
};
struct Heater : HeaterControllerBase {
    Heater():HeaterControllerBase(0,5,60) { Configure(780,300); }
    mutable float duty=0;
    void SetDuty(float d) const override { duty=d; }
};
int main() {
    for (float esr : {300.f, 250.f, 200.f}) {
        Timer::setMockTime(0);
        Heater h;
        Sample s;
        // Already-hot sensor enters closed loop after preheat->ramp->closed loop.
        for(int i=0;i<4;++i) {
            Timer::advanceMockTime(50000);
            h.Update(s,HeaterAllow::Allowed);
        }
        s.esr=esr;
        // Exact production LSU49 temperature table pairs (sampling.cpp).
        s.temp = esr==200 ? 840 : esr==250 ? 806 : 780;
        for(int i=0;i<40;++i) {
            Timer::advanceMockTime(50000);
            h.Update(s,HeaterAllow::Allowed);
            if(i==0 || i==39)
                std::printf("ESR=%.0f temp=%.0f after=%dms state=%d raw_duty=%.6f clipped_duty=%.6f telemetry_voltage=%.3f\n",
                    esr,s.temp,(i+1)*50,int(h.GetHeaterState()),h.duty,
                    std::clamp(h.duty,0.f,1.f),h.GetHeaterEffectiveVoltage());
        }
    }
}
