#include "fw.h"
/* OPT: RB_SIZE is a power of two -> wrap with a mask instead of compare/branch */
#define MASK (RB_SIZE - 1u)
void rb_init(rb_t *r) { r->head = 0; r->tail = 0; r->count = 0; }
void rb_push(rb_t *r, uint16_t v) {
    r->buf[r->head] = v;
    r->head = (uint8_t)((r->head + 1u) & MASK);
    if (r->count < RB_SIZE) r->count++;
    else r->tail = (uint8_t)((r->tail + 1u) & MASK);
}
int rb_pop(rb_t *r, uint16_t *out) {
    if (r->count == 0) return 0;
    *out = r->buf[r->tail];
    r->tail = (uint8_t)((r->tail + 1u) & MASK);
    r->count--;
    return 1;
}
