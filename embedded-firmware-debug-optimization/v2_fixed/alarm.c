#include "fw.h"
#define HYST_X10 20
static int thr_x10 = 400;                        /* FIX 5: signed type */
static int state;                                /* FIX 4: persistent, initialised */
void alarm_init(void) { thr_x10 = 400; state = 0; }
void alarm_set_thr_x10(int v) { thr_x10 = v; }
int  alarm_get_thr_x10(void)  { return thr_x10; }
int alarm_update(int t_x10) {
    if (t_x10 > thr_x10) state = 1;
    else if (t_x10 < thr_x10 - HYST_X10) state = 0;
    return state;                                /* inside the band: keep previous state */
}
