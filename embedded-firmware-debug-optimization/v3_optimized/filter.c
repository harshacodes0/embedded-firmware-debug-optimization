#include "fw.h"
/* OPT: running sum -> O(1) per sample, no loop, shift instead of divide once full */
static uint16_t win[MA_WIN];
static uint32_t sum;
static uint8_t  pos, filled;
void ma_init(void) { pos = 0; filled = 0; sum = 0; }
uint16_t ma_update(uint16_t x) {
    if (filled < MA_WIN) { sum += x; filled++; win[pos] = x; pos = (uint8_t)((pos + 1u) & (MA_WIN - 1u));
        return (uint16_t)(sum / filled); }              /* warm-up only (first 32 samples) */
    sum += x; sum -= win[pos]; win[pos] = x;
    pos = (uint8_t)((pos + 1u) & (MA_WIN - 1u));
    return (uint16_t)(sum >> 5);                        /* MA_WIN == 32 */
}
