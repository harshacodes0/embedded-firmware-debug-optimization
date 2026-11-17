#include <math.h>
#include "fw.h"
int thermo_adc_to_x10(uint16_t adc, int *t_x10) {
    if (adc <= ADC_FAULT_LO || adc >= ADC_FAULT_HI) { *t_x10 = 0; return -1; }   /* FIX 3 */
    float r  = 10000.0f * (float)adc / (4095.0f - (float)adc);
    float lr = logf(r / 10000.0f);
    float tc = 1.0f / (1.0f / 298.15f + lr / 3950.0f) - 273.15f;
    float x  = tc * 10.0f;
    *t_x10 = (int)(x >= 0.0f ? x + 0.5f : x - 0.5f);        /* round to nearest */
    return 0;
}
