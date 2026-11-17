/* Minimal HAL for QEMU lm3s6965evb (Cortex-M3, no FPU) */
#include "hal.h"
#include "adc_trace.h"
#define UART0_DR   (*(volatile uint32_t *)0x4000C000u)
#define SYST_CSR   (*(volatile uint32_t *)0xE000E010u)
#define SYST_RVR   (*(volatile uint32_t *)0xE000E014u)
#define SYST_CVR   (*(volatile uint32_t *)0xE000E018u)
#define SYSCLK_HZ  12000000u
#define RELOAD     (SYSCLK_HZ / 1000u - 1u)          /* 1 ms tick */

static volatile uint32_t g_ms;
extern void app_tick(void);                          /* defined in main.c */
void SysTick_Handler(void) { g_ms++; app_tick(); }

void hal_init(void) { SYST_RVR = RELOAD; SYST_CVR = 0; SYST_CSR = 7u; }
void hal_uart_puts(const char *s) { while (*s) UART0_DR = (uint8_t)*s++; }
static uint32_t g_idx;
uint16_t hal_adc_read(void) { uint16_t v = g_adc_trace[g_idx]; g_idx = (g_idx + 1u) % TRACE_LEN; return v; }
uint32_t hal_timer_read(void) {                      /* monotonic ticks since boot */
    uint32_t m1, v, m2;
    do { m1 = g_ms; v = SYST_CVR; m2 = g_ms; } while (m1 != m2);
    return m1 * (RELOAD + 1u) + (RELOAD - v);
}
void hal_exit(int code) {                            /* ARM semihosting SYS_EXIT */
    register uint32_t r0 __asm__("r0") = 0x18u;
    register uint32_t r1 __asm__("r1") = code ? 0x20023u : 0x20026u;
    __asm__ volatile("bkpt 0xAB" : : "r"(r0), "r"(r1) : "memory");
    for (;;) {}
}
void HardFault_Handler(void) {
    hal_uart_puts("\r\n[HARDFAULT]\r\n");
    hal_exit(2);
}
