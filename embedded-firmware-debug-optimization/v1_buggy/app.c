#include <stdio.h>
#include <stdlib.h>
#include "fw.h"
#include "hal.h"
uint32_t g_prof[N_STAGE];
static rb_t rb;
static const struct { int at; const char *cmd; } script[] = {
    { 100, "SET 38" }, { 200, "SET abc" }, { 260, "GET" }, { -1, 0 } };
void app_init(void) { rb_init(&rb); ma_init(); alarm_init(); }
void app_step(int i, app_out_t *o) {
    uint32_t t0 = hal_timer_read(), t1;
    uint16_t raw = hal_adc_read(), s = 0;
    rb_push(&rb, raw); rb_pop(&rb, &s);
    t1 = hal_timer_read(); g_prof[S_ACQ] += t1 - t0; t0 = t1;

    uint16_t avg = ma_update(s);
    t1 = hal_timer_read(); g_prof[S_FILT] += t1 - t0; t0 = t1;

    int tx10 = 0; thermo_adc_to_x10(avg, &tx10);
    t1 = hal_timer_read(); g_prof[S_CONV] += t1 - t0; t0 = t1;

    int al = alarm_update(tx10);
    t1 = hal_timer_read(); g_prof[S_ALARM] += t1 - t0; t0 = t1;

    for (int k = 0; script[k].at >= 0; k++)
        if (script[k].at == i) { char resp[16]; cmd_process(script[k].cmd, resp, sizeof resp); hal_uart_puts(resp); }
    if (i % 16 == 0) {
        char line[16];
        sprintf(line, "%d,%d.%d,%s\r\n", i, tx10 / 10, abs(tx10 % 10), al ? "ALARM" : "OK");  /* BUG 9 */
        hal_uart_puts(line);
    }
    t1 = hal_timer_read(); g_prof[S_LOG] += t1 - t0;
    if (o) { o->raw = raw; o->avg = avg; o->t_x10 = tx10; o->alarm = al; o->fault = 0; }
}
