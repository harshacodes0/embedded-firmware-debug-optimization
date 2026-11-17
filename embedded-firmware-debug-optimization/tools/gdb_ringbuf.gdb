set pagination off
set confirm off
set print pretty off
target remote localhost:1234
break rb_push if r->head == 64
continue
printf "--- stopped: head==64 (should be impossible: valid indices are 0..63)\n"
bt 3
print *r
printf "--- executing the store r->buf[r->head] = v  (v = %u)\n", v
next
print *r
printf "--- head/tail were overwritten by the sample bytes: head=%u tail=%u\n", r->head, r->tail
info line ringbuf.c:5
quit
