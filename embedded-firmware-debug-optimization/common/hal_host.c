/* Host HAL (x86-64 Linux) so the same application code can be tested with
   sanitizers, valgrind, gprof and unit tests. */
#define _POSIX_C_SOURCE 200809L
#include "hal.h"
#include "adc_trace.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
void hal_init(void) {}
void hal_uart_puts(const char *s) { fputs(s, stdout); }
static uint32_t g_idx;
uint16_t hal_adc_read(void) { uint16_t v = g_adc_trace[g_idx]; g_idx = (g_idx + 1u) % TRACE_LEN; return v; }
uint32_t hal_timer_read(void) {
    struct timespec ts; clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint32_t)(ts.tv_sec * 1000000000ull + ts.tv_nsec);
}
void hal_exit(int code) { exit(code); }
