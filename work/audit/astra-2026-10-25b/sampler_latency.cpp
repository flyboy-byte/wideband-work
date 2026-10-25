// Audit-only deterministic stimuli into unchanged production sampler/heater.
// This is NOT a physical sensor/disconnect/thermal-plant model.
#include <cassert>
#include <cmath>
#include <cstdio>
#include "sampling.h"
#include "heater_control.h"
#include "port.h"
#include "status.h"
SensorType GetSensorType() { return SensorType::LSU49; }
int GetESRSupplyR() { return 22000; }
float GetRemoteBatteryVoltage() { return 13; }
void SetStatus(int, wbo::Status) {}
struct Heater final:HeaterControllerBase {
    Heater():HeaterControllerBase(0,HEATER_PREHEAT_TIME,HEATER_WARMUP_TIMEOUT) { Configure(780,300); }
    mutable float duty=-1;
    void SetDuty(float d) const override { duty=d; }
};
float amplitude(float esr) { return VCC_VOLTS*(esr+VM_RESISTOR_VALUE)/(22000+esr+VM_RESISTOR_VALUE); }
bool valid(const Sampler& s,const Heater& h) {
    // Explicit copy of auxout.cpp validity predicate with lambda fixed1.0.
    // Actual auxout.cpp is covered separately by the21 shipped host tests.
    return s.GetNernstDc()>.35f && s.GetNernstDc()<.55f && h.IsRunningClosedLoop();
}
void run(const char* label,int period,int phase,bool dcFault,bool stall) {
    Timer::setMockTime(0); Sampler sampler; sampler.Init(); Heater heater;
    auto sample=[&](int i,float esr,float dc) {
        AnalogChannelResult v{};
        v.NernstVoltage=dc+(i%2 ? 1:-1)*amplitude(esr)/2;
        v.PumpCurrentVoltage=1.65f;
        assert(v.NernstVoltage>=0 && v.NernstVoltage<=VCC_VOLTS/NERNST_INPUT_GAIN);
        sampler.ApplySample(v,1.65f);
    };
    for(int i=0;i<10000;i++) sample(i,300,.45f);
    Timer::setMockTime(10000000);
    for(int i=0;i<10;i++) { Timer::advanceMockTime(50000); heater.Update(sampler,HeaterAllow::Allowed); }
    assert(valid(sampler,heater));
    int underheat=-1,zeroTemp=-1,invalid=-1,stop=-1,samples=0;
    for(int t=period;t<=2000000;t+=period) {
        Timer::advanceMockTime(period);
        if(!stall) { sample(samples++,dcFault?300:6000,dcFault?1.0f:.45f); }
        if(sampler.GetSensorTemperature()<680 && underheat<0) underheat=t;
        if(sampler.GetSensorTemperature()==0 && zeroTemp<0) zeroTemp=t;
        if((t+phase)%50000==0) heater.Update(sampler,HeaterAllow::Allowed);
        if(!valid(sampler,heater) && invalid<0) invalid=t;
        if(heater.GetHeaterState()==HeaterState::Stopped && stop<0) stop=t;
    }
    if(stall) { assert(invalid<0 && stop<0); }
    else if(dcFault) { assert(invalid>0 && invalid<=3*period); }
    else { assert(underheat>0 && invalid>0 && stop>0 && invalid<700000); assert(heater.duty==0); }
    std::printf("%s,dt_us=%d,heater_phase_us=%d,underheat_us=%d,zero_temp_us=%d,invalid_predicate_us=%d,heater_stop_us=%d\n",label,period,phase,underheat,zeroTemp,invalid,stop);
}
int main() {
    std::puts("Assumed sample intervals, NOT a measured ADC cadence. lambda=1.0 fixed; no analog output settling model.");
    for(int dt:{100,400,1000}) {
        for(int phase:{0,24000,49000}) {
            // Keep scheduler phases exact multiples of dt for this fixture.
            const int aligned=phase/dt*dt;
            run("ESR300_to6000_DCunchanged",dt,aligned,false,false);
            run("DC045_to100",dt,aligned,true,false);
        }
    }
    run("ADC_stall_last_valid",400,0,false,true);
    std::puts("19 stimulus/schedule cases passed assertions.");
}
