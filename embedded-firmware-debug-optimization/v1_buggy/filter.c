#include "fw.h"
static uint16_t win[MA_WIN];
static uint8_t  pos, filled;
void ma_init(void) { pos = 0; filled = 0; }
uint16_t ma_update(uint16_t x) {
    win[pos] = x;
    pos = (pos + 1) % MA_WIN;
    if (filled < MA_WIN) filled++;
    uint16_t sum = 0;                            /* BUG 2: 32*4095 overflows 16 bits */
    for (int i = 0; i < filled; i++)             /* O(N) every sample                */
        sum += win[i];
    return sum / filled;                         /* run-time division                */
}
