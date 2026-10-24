.syntax unified
// ARMv6-M instructions only, so the same entry runs on the Cortex-M0 (f0_module) and the Cortex-M3 (f1 boards). The
// earlier version was assembled for cortex-m3 (tst.w, ITE, b.w): on the M0 the first instruction faulted again inside
// HardFault and the core locked up, so HardFault_Handler_C and its reset never ran (work/docs/firmware.md, F9).
.cpu    cortex-m0
.thumb
.align  2

// r0 = the stacked exception frame: PSP if bit 2 of EXC_RETURN (in LR) is set, else MSP. Then jump to the C handler.
.macro FAULT_ENTRY handler
	movs r0, #4
	mov r1, lr
	tst r0, r1
	beq 1f
	mrs r0, PSP
	b 2f
1:
	mrs r0, MSP
2:
	ldr r1, =\handler
	bx r1
.endm

.type HardFault_Handler, %function
.type BusFault_Handler, %function
.type UsageFault_Handler, %function
.type MemManage_Handler, %function

.global HardFault_Handler
.global BusFault_Handler
.thumb_func
HardFault_Handler:
.thumb_func
BusFault_Handler:
	FAULT_ENTRY HardFault_Handler_C

.global UsageFault_Handler
.thumb_func
UsageFault_Handler:
	FAULT_ENTRY UsageFault_Handler_C

.global MemManage_Handler
.thumb_func
MemManage_Handler:
	FAULT_ENTRY MemManage_Handler_C

.ltorg
