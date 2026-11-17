#include "fw.h"
#include "thermo_lut.h"
/* OPT: 257-entry int16 table (514 B in flash) + linear interpolation replaces
   float division + logf() + soft-float emulation on an FPU-less Cortex-M3.   */
int thermo_adc_to_x10(uint16_t adc, int *t_x10) {
    if (adc <= ADC_FAULT_LO || adc >= ADC_FAULT_HI) { *t_x10 = 0; return -1; }
    unsigned i = adc >> LUT_SHIFT, f = adc & ((1u << LUT_SHIFT) - 1u);
    int a = g_lut[i], b = g_lut[i + 1];
    *t_x10 = a + (((b - a) * (int)f + (1 << (LUT_SHIFT - 1))) >> LUT_SHIFT);
    return 0;
}
