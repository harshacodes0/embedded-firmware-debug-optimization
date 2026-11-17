#ifndef HAL_H
#define HAL_H
#include <stdint.h>
void     hal_init(void);
void     hal_uart_puts(const char *s);
uint16_t hal_adc_read(void);       /* next sample of the recorded trace      */
uint32_t hal_timer_read(void);     /* free-running timestamp, core-clock ticks */
void     hal_exit(int code);       /* semihosting exit (QEMU) / exit() (host)  */
#endif
