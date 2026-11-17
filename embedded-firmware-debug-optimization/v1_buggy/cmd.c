#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "fw.h"
int cmd_process(const char *line, char *resp, size_t n) {
    (void)n;
    char arg[8];
    if (strncmp(line, "SET ", 4) == 0) {
        strcpy(arg, line + 4);                   /* BUG 6: unbounded copy        */
        alarm_set_thr_x10(atoi(arg) * 10);       /* BUG 7: no validation / range */
        strcpy(resp, "OK\r\n");
        return 0;
    }
    if (strcmp(line, "GET") == 0) {
        int t = alarm_get_thr_x10();
        sprintf(resp, "THR=%d.%d\r\n", t / 10, t % 10);   /* BUG 8: unbounded */
        return 0;
    }
    strcpy(resp, "ERR\r\n");
    return -1;
}
