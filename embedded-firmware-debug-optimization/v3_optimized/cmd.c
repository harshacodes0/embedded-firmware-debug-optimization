#include "fw.h"
/* OPT: no stdio/snprintf -> removes newlib-nano printf (~KBs of flash) */
static size_t cat(char *d, size_t n, size_t k, const char *s) { while (*s && k + 1 < n) d[k++] = *s++; d[k] = 0; return k; }
static int parse_thr(const char *s, int *out) {
    int v = 0, digits = 0;
    while (*s >= '0' && *s <= '9') { v = v * 10 + (*s - '0'); if (++digits > 3) return -1; s++; }
    if (digits == 0 || *s != '\0' || v > 125) return -1;
    *out = v; return 0;
}
static int starts(const char *s, const char *p) { while (*p) if (*s++ != *p++) return 0; return 1; }
int cmd_process(const char *line, char *resp, size_t n) {
    int v;
    if (starts(line, "SET ")) {
        if (parse_thr(line + 4, &v) != 0) { cat(resp, n, 0, "ERR\r\n"); return -1; }
        alarm_set_thr_x10(v * 10); cat(resp, n, 0, "OK\r\n"); return 0;
    }
    if (line[0]=='G' && line[1]=='E' && line[2]=='T' && line[3]==0) {
        int t = alarm_get_thr_x10(); char d[4]; size_t k = cat(resp, n, 0, "THR=");
        int ip = t / 10; d[0] = (char)('0' + ip / 100); d[1] = (char)('0' + (ip / 10) % 10); d[2] = (char)('0' + ip % 10); d[3] = 0;
        const char *p = d; while (p[0] == '0' && p[1]) p++;
        k = cat(resp, n, k, p); d[0] = '.'; d[1] = (char)('0' + t % 10); d[2] = 0;
        k = cat(resp, n, k, d); cat(resp, n, k, "\r\n"); return 0;
    }
    cat(resp, n, 0, "ERR\r\n"); return -1;
}
