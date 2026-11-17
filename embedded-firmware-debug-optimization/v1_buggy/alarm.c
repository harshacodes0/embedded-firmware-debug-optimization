#include "fw.h"
static uint32_t thr_x10 = 400;                   /* 40.0 C */
void alarm_init(void) { thr_x10 = 400; }
void alarm_set_thr_x10(int v) { thr_x10 = v; }
int  alarm_get_thr_x10(void)  { return (int)thr_x10; }
int alarm_update(int t_x10) {
    int state;                                   /* BUG 4: uninitialised in hysteresis band */
    if (t_x10 > thr_x10) state = 1;              /* BUG 5: signed/unsigned compare          */
    else if (t_x10 < thr_x10 - 20) state = 0;
    return state;
}
