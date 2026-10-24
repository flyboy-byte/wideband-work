/* Minimal Cortex-M0 harness for main_hardfault_asm.S on QEMU microbit. Prints via semihosting. */
#include <stdint.h>
static void sh_write0(const char* s) {
    register int r0 __asm__("r0") = 4; register const char* r1 __asm__("r1") = s;
    __asm__ volatile("bkpt 0xab" : "+r"(r0) : "r"(r1) : "memory");
}
static void sh_exit(int ok) {
    register int r0 __asm__("r0") = 0x18; register int r1 __asm__("r1") = ok ? 0x20026 : 0x20023;
    __asm__ volatile("bkpt 0xab" : "+r"(r0) : "r"(r1) : "memory");
    for (;;) {}
}
void HardFault_Handler_C(void* sp) {
    (void)sp;
    sh_write0("REACHED HardFault_Handler_C\n");
#ifdef DO_BKPT
    sh_write0("executing BKPT #0 like upstream's bkpt(), no debugger attached\n");
    __asm__ volatile("BKPT #0\n");
    sh_write0("returned from BKPT #0\n");
#endif
    sh_exit(1);
}
void UsageFault_Handler_C(void* sp) { (void)sp; sh_write0("usage C\n"); sh_exit(0); }
void MemManage_Handler_C(void* sp) { (void)sp; sh_write0("memmanage C\n"); sh_exit(0); }
void Default_Handler(void) { sh_write0("default handler\n"); sh_exit(0); }
void Reset_Handler(void) {
    sh_write0("reset: executing UDF to force a HardFault\n");
    __asm__ volatile("udf #0");
    sh_write0("after UDF (unexpected)\n");
    sh_exit(0);
}
extern void HardFault_Handler(void);
__attribute__((section(".vectors"), used)) void (*const vectors[16])(void) = {
    (void (*)(void))0x20001000, Reset_Handler, Default_Handler, HardFault_Handler,
    0, 0, 0, 0, 0, 0, 0, Default_Handler, 0, 0, Default_Handler, Default_Handler };
