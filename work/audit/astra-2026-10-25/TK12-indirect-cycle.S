.syntax unified
.cpu cortex-m0
.thumb
.section .text
.global _Z12HeaterThreadPv
.type _Z12HeaterThreadPv,%function
.thumb_func
_Z12HeaterThreadPv:
push {r4,lr}
bl deep_helper
pop {r4,pc}
.size _Z12HeaterThreadPv, .-_Z12HeaterThreadPv
.ltorg
.global deep_helper
.type deep_helper,%function
.thumb_func
deep_helper:
push {r4,lr}
sub sp, #100
ldr r3, =deep_helper
blx r3
add sp, #100
pop {r4,pc}
.size deep_helper, .-deep_helper
.global _Z10PumpThreadPv
.type _Z10PumpThreadPv,%function
.thumb_func
_Z10PumpThreadPv:
bx lr
.size _Z10PumpThreadPv, .-_Z10PumpThreadPv
.global _Z14SamplingThreadPv
.type _Z14SamplingThreadPv,%function
.thumb_func
_Z14SamplingThreadPv:
bx lr
.size _Z14SamplingThreadPv, .-_Z14SamplingThreadPv
.global _Z11CanTxThreadPv
.type _Z11CanTxThreadPv,%function
.thumb_func
_Z11CanTxThreadPv:
bx lr
.size _Z11CanTxThreadPv, .-_Z11CanTxThreadPv
.global _Z11CanRxThreadPv
.type _Z11CanRxThreadPv,%function
.thumb_func
_Z11CanRxThreadPv:
bx lr
.size _Z11CanRxThreadPv, .-_Z11CanRxThreadPv
.global main
.type main,%function
.thumb_func
main:
bx lr
.size main, .-main
.global __main_thread_stack_base__, __main_thread_stack_end__, __main_stack_base__, __main_stack_end__
.set __main_thread_stack_base__,0x20000000
.set __main_thread_stack_end__,0x20000200
.set __main_stack_base__,0x20000200
.set __main_stack_end__,0x20000400

.ltorg
