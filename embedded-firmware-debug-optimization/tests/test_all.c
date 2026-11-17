/* Host-side regression tests, identical for v1_buggy / v2_fixed / v3_optimized.
 *   ./t            run every test in this process
 *   ./t <name>     run one test (used by run_tests.sh so a crash only kills one test)
 *   ./t csv        dump the 512-sample application trace as CSV
 *   ./t bench      host timing of the per-stage profile (ns per sample)
 */
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "fw.h"
#include "hal.h"
#include "adc_trace.h"

static int fails;
#define CHECK(cond, ...) do { if (!(cond)) { printf("    expected: %s  (", #cond); printf(__VA_ARGS__); printf(")\n"); return 1; } } while (0)

static int t_ringbuf_fifo(void) {            /* push/pop 200 samples one at a time */
    rb_t r; rb_init(&r); uint16_t v;
    for (uint16_t i = 0; i < 200; i++) {
        rb_push(&r, (uint16_t)(1000 + i));
        CHECK(rb_pop(&r, &v) == 1, "pop failed at i=%u", i);
        CHECK(v == 1000 + i, "i=%u got %u", i, v);
    }
    return 0;
}
static int t_ringbuf_overwrite(void) {       /* fill beyond capacity: oldest are dropped */
    rb_t r; rb_init(&r); uint16_t v;
    for (uint16_t i = 0; i < 100; i++) rb_push(&r, i);
    CHECK(r.count == RB_SIZE, "count=%u", r.count);
    CHECK(rb_pop(&r, &v) == 1 && v == 36, "oldest=%u (expected 36)", v);
    return 0;
}
static int t_filter_constant(void) {         /* DC input must pass unchanged */
    ma_init(); uint16_t y = 0;
    for (int i = 0; i < 64; i++) y = ma_update(3000);
    CHECK(y == 3000, "avg of 3000s = %u", y);
    return 0;
}
static int t_filter_fullscale(void) {
    ma_init(); uint16_t y = 0;
    for (int i = 0; i < 64; i++) y = ma_update(4095);
    CHECK(y == 4095, "avg of 4095s = %u", y);
    return 0;
}
static int t_thermo_fault(void) {
    int t;
    CHECK(thermo_adc_to_x10(0, &t) == -1, "adc=0 must be a fault");
    CHECK(thermo_adc_to_x10(4095, &t) == -1, "adc=4095 must be a fault");
    return 0;
}
static int t_thermo_accuracy(void) {         /* vs double-precision formula, -40..125 C */
    int worst = 0, wa = 0;
    for (int adc = 142; adc <= 3995; adc++) {
        int t; if (thermo_adc_to_x10((uint16_t)adc, &t) != 0) { printf("    fault at %d\n", adc); return 1; }
        double r = 10000.0 * adc / (4095.0 - adc);
        double ref = (1.0 / (1.0 / 298.15 + log(r / 10000.0) / 3950.0) - 273.15) * 10.0;
        int e = (int)lround(fabs(t - ref)); if (e > worst) { worst = e; wa = adc; }
    }
    printf("    max error %.1f C at adc=%d\n", worst / 10.0, wa);
    CHECK(worst <= 2, "max error %d x0.1C", worst);
    return 0;
}
static int t_alarm_negative_temp(void) {     /* a cold reading must never raise the alarm */
    alarm_init(); CHECK(alarm_update(-80) == 0, "-8.0 C raised alarm");
    return 0;
}
static int t_alarm_hysteresis(void) {
    alarm_init();
    CHECK(alarm_update(405) == 1, "should trip above 40.0");
    CHECK(alarm_update(390) == 1, "must hold inside 2.0 C band");
    CHECK(alarm_update(370) == 0, "must clear below 38.0");
    CHECK(alarm_update(390) == 0, "must stay clear inside band");
    return 0;
}
static int t_cmd_set_valid(void) {
    char resp[16]; alarm_init();
    CHECK(cmd_process("SET 38", resp, sizeof resp) == 0, "SET 38 rejected");
    CHECK(alarm_get_thr_x10() == 380, "thr=%d", alarm_get_thr_x10());
    return 0;
}
static int t_cmd_set_garbage(void) {
    char resp[16]; alarm_init();
    CHECK(cmd_process("SET abc", resp, sizeof resp) == -1, "garbage accepted");
    CHECK(alarm_get_thr_x10() == 400, "threshold changed to %d", alarm_get_thr_x10());
    return 0;
}
static int t_cmd_set_range(void) {
    char resp[16]; alarm_init();
    CHECK(cmd_process("SET 200", resp, sizeof resp) == -1, "200 C accepted");
    CHECK(alarm_get_thr_x10() == 400, "threshold changed to %d", alarm_get_thr_x10());
    return 0;
}
static int t_cmd_long_input(void) {          /* 40-char argument into an 8-byte buffer */
    char resp[16]; alarm_init();
    cmd_process("SET 1234567890123456789012345678901234567890", resp, sizeof resp);
    CHECK(alarm_get_thr_x10() == 400, "threshold changed to %d", alarm_get_thr_x10());
    return 0;
}
static int t_cmd_get(void) {
    char resp[16]; alarm_init(); cmd_process("GET", resp, sizeof resp);
    CHECK(strcmp(resp, "THR=40.0\r\n") == 0, "resp='%s'", resp);
    return 0;
}
static int t_app_trace(void) {               /* whole pipeline over the recorded trace */
    app_out_t o; app_init(); int alarms_in_cold = 0, faults = 0, bad = 0;
    for (int i = 0; i < TRACE_LEN; i++) {
        app_step(i, &o);
        if (i < 40 && o.alarm) alarms_in_cold++;           /* first 40 samples are ~ -8..-7 C */
        if (o.fault) faults++;
        if (o.t_x10 < -100 || o.t_x10 > 600) bad++;        /* plausible range -10..60 C       */
    }
    CHECK(alarms_in_cold == 0, "%d false alarms while cold", alarms_in_cold);
    CHECK(faults == 2, "faults detected = %d (expected 2)", faults);
    CHECK(bad == 0, "%d samples outside -10..60 C", bad);
    return 0;
}

static const struct { const char *name; int (*fn)(void); } tests[] = {
    {"ringbuf_fifo", t_ringbuf_fifo}, {"ringbuf_overwrite", t_ringbuf_overwrite},
    {"filter_constant", t_filter_constant}, {"filter_fullscale", t_filter_fullscale},
    {"thermo_fault", t_thermo_fault}, {"thermo_accuracy", t_thermo_accuracy},
    {"alarm_negative_temp", t_alarm_negative_temp}, {"alarm_hysteresis", t_alarm_hysteresis},
    {"cmd_set_valid", t_cmd_set_valid}, {"cmd_set_garbage", t_cmd_set_garbage},
    {"cmd_set_range", t_cmd_set_range}, {"cmd_long_input", t_cmd_long_input},
    {"cmd_get", t_cmd_get}, {"app_trace", t_app_trace}, {0, 0} };

int main(int argc, char **argv) {
    if (argc > 1 && !strcmp(argv[1], "csv")) {
        app_out_t o; app_init(); printf("i,raw,avg,t_x10,alarm,fault\n");
        for (int i = 0; i < TRACE_LEN; i++) { app_step(i, &o); printf("%d,%u,%u,%d,%d,%d\n", i, o.raw, o.avg, o.t_x10, o.alarm, o.fault); }
        return 0;
    }
    if (argc > 1 && !strcmp(argv[1], "bench")) {
        static const char *nm[] = {"acq", "filt", "conv", "alarm", "log"};
        enum { PASSES = 200 };
        app_init(); for (int p = 0; p < PASSES; p++) for (int i = 0; i < TRACE_LEN; i++) app_step(i, 0);
        fprintf(stderr, "ns/sample:"); uint32_t tot = 0;
        for (int k = 0; k < N_STAGE; k++) { fprintf(stderr, " %s=%.1f", nm[k], (double)g_prof[k] / (PASSES * TRACE_LEN)); tot += g_prof[k]; }
        fprintf(stderr, " total=%.1f\n", (double)tot / (PASSES * TRACE_LEN)); return 0;
    }
    int ran = 0;
    for (int k = 0; tests[k].name; k++) {
        if (argc > 1 && strcmp(argv[1], tests[k].name)) continue;
        int rc = tests[k].fn(); ran++; fails += rc;
        printf("[%s] %s\n", rc ? "FAIL" : "PASS", tests[k].name); fflush(stdout);
    }
    if (!ran) { printf("no such test\n"); return 2; }
    printf("%d test(s), %d failed\n", ran, fails);
    return fails ? 1 : 0;
}
