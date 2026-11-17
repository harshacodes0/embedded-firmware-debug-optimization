#include "hal.h"
void app_tick(void) {}
static void put_u(uint32_t v){char b[11];int n=0;do{b[n++]=(char)(48+v%10);v/=10;}while(v);char o[12];int k=0;while(n)o[k++]=b[--n];o[k]=0;hal_uart_puts(o);}
__attribute__((noinline)) static void blk2k(void){ __asm__ volatile(".rept 2000\n nop\n .endr"); }
__attribute__((noinline)) static void blk6k(void){ __asm__ volatile(".rept 6000\n nop\n .endr"); }
int main(void){ hal_init();
 uint32_t t0=hal_timer_read(); blk2k(); uint32_t t1=hal_timer_read();
 hal_uart_puts("nop2000 ticks="); put_u(t1-t0); hal_uart_puts("\r\n");
 t0=hal_timer_read(); blk6k(); t1=hal_timer_read();
 hal_uart_puts("nop6000 ticks="); put_u(t1-t0); hal_uart_puts("\r\n");
 uint32_t sum=0; for(int i=0;i<512;i++){ uint32_t a=hal_timer_read(); uint32_t b=hal_timer_read(); sum+=b-a; }
 hal_uart_puts("timer_read_overhead_total_512="); put_u(sum); hal_uart_puts("\r\n"); return 0; }
