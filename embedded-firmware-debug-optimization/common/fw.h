#ifndef FW_H
#define FW_H
#include <stdint.h>
#include <stddef.h>
#define RB_SIZE      64
#define MA_WIN       32
#define ADC_FAULT_LO 10      /* <=  short-circuit  */
#define ADC_FAULT_HI 4085    /* >=  open-circuit   */
typedef struct { uint16_t buf[RB_SIZE]; uint8_t head, tail, count; } rb_t;
void     rb_init(rb_t *r);
void     rb_push(rb_t *r, uint16_t v);
int      rb_pop(rb_t *r, uint16_t *out);              /* 1 = got value        */
void     ma_init(void);
uint16_t ma_update(uint16_t x);                       /* 32-sample moving avg */
int      thermo_adc_to_x10(uint16_t adc, int *t_x10); /* 0 ok, -1 sensor fault*/
void     alarm_init(void);
int      alarm_update(int t_x10);                     /* 1 = alarm active     */
void     alarm_set_thr_x10(int v);
int      alarm_get_thr_x10(void);
int      cmd_process(const char *line, char *resp, size_t n);
typedef struct { uint16_t raw, avg; int t_x10; int alarm; int fault; } app_out_t;
enum { S_ACQ, S_FILT, S_CONV, S_ALARM, S_LOG, N_STAGE };
extern uint32_t g_prof[N_STAGE];                      /* per-stage tick totals */
void app_init(void);
void app_step(int i, app_out_t *o);
#endif
