# TK1: narrowed stack targets

Reviewed18b6cef with pinned ChibiOS a8865dc,libfirmware39b3a04 and ARM GCC16.2. Fresh package built in/tmp/wb-round7-package;21616Bapp,CRC984fc2b4. `TK1-stack.log` reproduces heater/pump148/256B,sampling164/256B,CanTx284/512B,CanRx220/512B,main188/1024B,single interrupt156/1024B. Four regressions pass, including the prior actual indirect-recursion case with-v, no hang.

MEASURED `stack_inventory.py` finds15callers/40BLX sites: five narrowed callers13sites, ten remaining callers27sites. Source justification for each narrowing:

| Caller | Complete current source target set | Evidence |
| --- | --- | --- |
|HeaterControllerBase::Update|Sampler's six interface methods plusHeaterController::SetDuty|heater_control.cpp:197-259;sampling.h;heater_thread.cpp:29-64;only one concrete sampler/heater type linked|
|Sampler::GetSensorTemperature|GetSensorInternalResistance,GetNernstAc|sampling.cpp:63-89; compiler fallback dispatches through the same object|
|Sampler::GetSensorInternalResistance|GetNernstAc|sampling.cpp:82-89|
|__port_thread_start|thread entry accounted on its own stack; no retained caller frame|ChibiOS chcoreasm.S:101-115; `blx r4` is entry dispatch, startup makes no push/sub frame|
|adc_lld_serve_rx_interrupt|adcDoneCallback|ADCv1/hal_adc_lld.c:123-149 and hal_adc.h callback macros;f0 port.cpp:27-37 group has end_cb=adcDoneCallback,error_cb=null;only ADCD1/that group used|

DOCUMENTED: firmware search and ELF vtables identify only Sampler and HeaterController as the concrete objects for these virtual interfaces in this f0 build. Other callers retain all22address-taken targets, an over-approximation for the linked static function pointers/vtables. The recursive regression now fails as unbounded; cycles are no longer discarded. Literal-pool checks are useful consistency tests but are not sufficient to prove a virtual target set: future source changes need this source review again. Current classes/configuration, not the guard alone, justify narrowing.

Answer on92B: **yes as a conservative bound for the checked current thread paths under these source/table assumptions; no as an unqualified whole-processor stack guarantee**. Context pushes are charged conservatively; ChibiOS PORT_WA_SIZE also reserves context/interrupt overhead outside the user n. No runtime watermark claimed.

Startup: ELF.xtors has one pointer0x080057f1 to_sub_I_65535_0.0; disassembly shows20Bpush and no calls/indirect calls, so no hidden deep constructor. Startup uses configured PSP/main stack1024B (CRT0_CONTROL_INIT), not a256Bworker stack. This is a manual checked exception to the checker's omission, not a newly implemented startup analysis.

Interrupts: current configured priorities used are2(ADC DMA/system timer) and3(CAN/PWM); normal same-priority handlers cannot preempt each other. Even a deliberately conservative four-level nesting allowance including HardFault/NMI at the reported156B software maximum plus32B hardware frame each is752B<1024B. This relies on current enabled priorities and the checked single-handler graph; it is not a generic guarantee for changed priorities, fault corruption or a different build. The92Bthread figure does not quantify this MSP reserve.

No new counterexample against the current narrowed production paths established. No checker or firmware files modified.
