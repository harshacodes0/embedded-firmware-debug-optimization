#include "fw.h"
#include "hal.h"
#include "adc_trace.h"
static uint8_t sample_due;                       /* BUG 10: shared with ISR but not volatile */
void app_tick(void) { sample_due = 1; }          /* called from SysTick ISR                  */
static void put_u(uint32_t v) { char b[11]; int n = 0; do { b[n++] = '0' + v % 10; v /= 10; } while (v); char o[12]; int k = 0; while (n) o[k++] = b[--n]; o[k] = 0; hal_uart_puts(o); }
int main(void) {
    hal_init(); app_init();
    hal_uart_puts("# v1 start\r\n");
    uint32_t t0 = hal_timer_read();
    for (int i = 0; i < TRACE_LEN; i++) {
        while (!sample_due) { }                  /* wait for 1 kHz tick */
        sample_due = 0;
        app_step(i, 0);
    }
    uint32_t t1 = hal_timer_read();
    hal_uart_puts("# done ticks="); put_u(t1 - t0); hal_uart_puts("\r\n");
    { static const char *nm[] = {"acq", "filt", "conv", "alarm", "log"};
      hal_uart_puts("# prof");
      for (int k = 0; k < N_STAGE; k++) { hal_uart_puts(" "); hal_uart_puts(nm[k]); hal_uart_puts("="); put_u(g_prof[k]); }
      hal_uart_puts("\r\n"); }
    return 0;
}
