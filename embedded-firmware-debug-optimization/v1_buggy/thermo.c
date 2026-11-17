#include <math.h>
#include "fw.h"
/* NTC 10k, B=3950, 10k pull-up, 12-bit ADC (NTC on the low side) */
int thermo_adc_to_x10(uint16_t adc, int *t_x10) {
    float r  = 10000.0f * (float)adc / (4095.0f - (float)adc);  /* BUG 3: /0 at 4095 */
    float lr = logf(r / 10000.0f);                              /* BUG 3: log(0)     */
    float tc = 1.0f / (1.0f / 298.15f + lr / 3950.0f) - 273.15f;
    *t_x10 = (int)(tc * 10.0f);                                 /* BUG 3: inf -> int */
    return 0;
}
