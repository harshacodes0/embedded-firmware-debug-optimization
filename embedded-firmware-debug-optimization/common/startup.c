/* Cortex-M3 start-up: vector table, .data copy, .bss clear */
#include <stdint.h>
extern uint32_t _estack, _sidata, _sdata, _edata, _sbss, _ebss;
extern int main(void);
extern void hal_exit(int);
void Reset_Handler(void);
void Default_Handler(void) { for (;;) {} }
void NMI_Handler(void)        __attribute__((weak, alias("Default_Handler")));
void HardFault_Handler(void)  __attribute__((weak, alias("Default_Handler")));
void MemManage_Handler(void)  __attribute__((weak, alias("HardFault_Handler")));
void BusFault_Handler(void)   __attribute__((weak, alias("HardFault_Handler")));
void UsageFault_Handler(void) __attribute__((weak, alias("HardFault_Handler")));
void SVC_Handler(void)        __attribute__((weak, alias("Default_Handler")));
void PendSV_Handler(void)     __attribute__((weak, alias("Default_Handler")));
void SysTick_Handler(void)    __attribute__((weak, alias("Default_Handler")));
typedef void (*vec_t)(void);
__attribute__((section(".isr_vector"), used))
const vec_t g_vectors[16] = {
    (vec_t)&_estack, Reset_Handler, NMI_Handler, HardFault_Handler,
    MemManage_Handler, BusFault_Handler, UsageFault_Handler, 0, 0, 0, 0,
    SVC_Handler, 0, 0, PendSV_Handler, SysTick_Handler };
void Reset_Handler(void) {
    uint32_t *s = &_sidata, *d = &_sdata;
    while (d < &_edata) *d++ = *s++;
    for (d = &_sbss; d < &_ebss; ) *d++ = 0;
    hal_exit(main());
}
