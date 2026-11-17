#include "fw.h"
void rb_init(rb_t *r) { r->head = 0; r->tail = 0; r->count = 0; }
void rb_push(rb_t *r, uint16_t v) {
    r->buf[r->head] = v;
    r->head++;
    if (r->head >= RB_SIZE) r->head = 0;         /* FIX 1: >= */
    if (r->count < RB_SIZE) r->count++;
    else { r->tail++; if (r->tail >= RB_SIZE) r->tail = 0; }
}
int rb_pop(rb_t *r, uint16_t *out) {
    if (r->count == 0) return 0;
    *out = r->buf[r->tail];
    r->tail++;
    if (r->tail >= RB_SIZE) r->tail = 0;
    r->count--;
    return 1;
}
