/* HAL for STM32F103C8 ("Blue Pill", Cortex-M3 @ 8 MHz HSI, no FPU).
 * STATUS: compiles and links (see `make stm32`). NOT yet run on a physical board by the
 * author of this repo -- flash it, open a serial terminal at 115200 8N1 on PA9 (USART1 TX)
 * and fill in the hardware table in the report.
 * hal_timer_read() returns DWT->CYCCNT, i.e. REAL core clock cycles.                         */
#include "hal.h"
#include "adc_trace.h"
#define RCC_APB2ENR (*(volatile uint32_t *)0x40021018u)
#define GPIOA_CRH   (*(volatile uint32_t *)0x40010804u)
#define USART1_SR   (*(volatile uint32_t *)0x40013800u)
#define USART1_DR   (*(volatile uint32_t *)0x40013804u)
#define USART1_BRR  (*(volatile uint32_t *)0x40013808u)
#define USART1_CR1  (*(volatile uint32_t *)0x4001380Cu)
#define SYST_CSR    (*(volatile uint32_t *)0xE000E010u)
#define SYST_RVR    (*(volatile uint32_t *)0xE000E014u)
#define SYST_CVR    (*(volatile uint32_t *)0xE000E018u)
#define DEMCR       (*(volatile uint32_t *)0xE000EDFCu)
#define DWT_CTRL    (*(volatile uint32_t *)0xE0001000u)
#define DWT_CYCCNT  (*(volatile uint32_t *)0xE0001004u)
#define SYSCLK_HZ   8000000u

extern void app_tick(void);
void SysTick_Handler(void) { app_tick(); }

void hal_init(void) {
    RCC_APB2ENR |= (1u << 2) | (1u << 14);                 /* GPIOA + USART1 clocks            */
    GPIOA_CRH = (GPIOA_CRH & ~(0xFu << 4)) | (0xBu << 4);  /* PA9: AF push-pull, 50 MHz        */
    USART1_BRR = SYSCLK_HZ / 115200u;                      /* 69 -> 115942 baud (0.6 % error)  */
    USART1_CR1 = (1u << 13) | (1u << 3);                   /* UE | TE                          */
    DEMCR |= (1u << 24); DWT_CYCCNT = 0; DWT_CTRL |= 1u;   /* enable cycle counter             */
    SYST_RVR = SYSCLK_HZ / 1000u - 1u; SYST_CVR = 0; SYST_CSR = 7u;  /* 1 kHz tick             */
}
void hal_uart_puts(const char *s) { while (*s) { while (!(USART1_SR & (1u << 7))) {} USART1_DR = (uint8_t)*s++; } }
static uint32_t g_idx;
uint16_t hal_adc_read(void) { uint16_t v = g_adc_trace[g_idx]; g_idx = (g_idx + 1u) % TRACE_LEN; return v; }
uint32_t hal_timer_read(void) { return DWT_CYCCNT; }
void hal_exit(int code) { (void)code; hal_uart_puts("# end\r\n"); for (;;) {} }
void HardFault_Handler(void) { hal_uart_puts("\r\n[HARDFAULT]\r\n"); for (;;) {} }
