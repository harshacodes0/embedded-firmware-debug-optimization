#include <stdio.h>
#include <string.h>
#include "fw.h"
/* parse "SET <0..125>" strictly; returns 0 ok, -1 error */
static int parse_thr(const char *s, int *out) {
    int v = 0, digits = 0;
    while (*s >= '0' && *s <= '9') { v = v * 10 + (*s - '0'); if (++digits > 3) return -1; s++; }
    if (digits == 0 || *s != '\0' || v > 125) return -1;     /* FIX 6/7 */
    *out = v; return 0;
}
static void put(char *resp, size_t n, const char *s) { snprintf(resp, n, "%s", s); }   /* FIX 8 */
int cmd_process(const char *line, char *resp, size_t n) {
    int v;
    if (strncmp(line, "SET ", 4) == 0) {
        if (parse_thr(line + 4, &v) != 0) { put(resp, n, "ERR\r\n"); return -1; }
        alarm_set_thr_x10(v * 10); put(resp, n, "OK\r\n"); return 0;
    }
    if (strcmp(line, "GET") == 0) {
        int t = alarm_get_thr_x10();
        snprintf(resp, n, "THR=%d.%d\r\n", t / 10, t % 10); return 0;
    }
    put(resp, n, "ERR\r\n"); return -1;
}
