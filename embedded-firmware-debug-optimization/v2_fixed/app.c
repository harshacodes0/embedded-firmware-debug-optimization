#include <stdio.h>
#include <stdlib.h>
#include "fw.h"
#include "hal.h"
uint32_t g_prof[N_STAGE];
static rb_t rb;
static uint16_t last_good = 2048;
static const struct { int at; const char *cmd; } script[] = {
    { 100, "SET 38" }, { 200, "SET abc" }, { 260, "GET" }, { -1, 0 } };
void app_init(void) { rb_init(&rb); ma_init(); alarm_init(); last_good = 2048; }
void app_step(int i, app_out_t *o) {
    uint32_t t0 = hal_timer_read(), t1;
    uint16_t raw = hal_adc_read(), s = 0;
    int fault = (raw <= ADC_FAULT_LO || raw >= ADC_FAULT_HI);     /* FIX 3: reject faulty sample */
    rb_push(&rb, fault ? last_good : raw); rb_pop(&rb, &s);
    if (!fault) last_good = raw;
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
        char line[32];                                            /* FIX 9 */
        const char *sg = tx10 < 0 ? "-" : "";                     /* FIX 9: keep sign for -0.x */
        int a = abs(tx10);
        snprintf(line, sizeof line, "%d,%s%d.%d,%s%s\r\n", i, sg, a / 10, a % 10, al ? "ALARM" : "OK", fault ? ",FLT" : "");
        hal_uart_puts(line);
    }
    t1 = hal_timer_read(); g_prof[S_LOG] += t1 - t0;
    if (o) { o->raw = raw; o->avg = avg; o->t_x10 = tx10; o->alarm = al; o->fault = fault; }
}
