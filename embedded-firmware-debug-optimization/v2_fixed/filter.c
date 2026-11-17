#include "fw.h"
static uint16_t win[MA_WIN];
static uint8_t  pos, filled;
void ma_init(void) { pos = 0; filled = 0; }
uint16_t ma_update(uint16_t x) {
    win[pos] = x;
    pos = (uint8_t)((pos + 1) % MA_WIN);
    if (filled < MA_WIN) filled++;
    uint32_t sum = 0;                            /* FIX 2: 32-bit accumulator */
    for (int i = 0; i < filled; i++) sum += win[i];
    return (uint16_t)(sum / filled);
}
