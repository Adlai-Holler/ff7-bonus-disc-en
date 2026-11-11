/* Longest-match finder for the 4 KB-window LZSS (len 3..18). Fills ml[i], mp[i] like npk.encode_opt. */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#define HBITS 16
void find_matches(const uint8_t *d, int n, int maxcand, int32_t *ml, int32_t *mp) {
    int32_t *head = malloc(sizeof(int32_t) << HBITS), *prev = malloc(sizeof(int32_t) * (n ? n : 1));
    for (int i = 0; i < (1 << HBITS); i++) head[i] = -1;
    for (int i = 0; i < n; i++) {
        ml[i] = 0; mp[i] = 0; prev[i] = -1;
        if (i + 3 > n) continue;
        uint32_t key = d[i] | (d[i+1] << 8) | (d[i+2] << 16);
        uint32_t h = (key * 2654435761u) >> (32 - HBITS);
        int lim = n - i < 18 ? n - i : 18, bl = 0, bp = 0, c = 0;
        for (int j = head[h]; j >= 0 && c < maxcand; j = prev[j], c++) {
            if (i - j > 4095 - 18) break;
            if (d[j] != d[i] || d[j+1] != d[i+1] || d[j+2] != d[i+2]) continue;
            int l = 3; while (l < lim && d[j+l] == d[i+l]) l++;
            if (l > bl) { bl = l; bp = j; if (l == lim) break; }
        }
        ml[i] = bl; mp[i] = bp;
        prev[i] = head[h]; head[h] = i;
    }
    free(head); free(prev);
}
/* optimal parse: choice[i] = 1 (literal) or match length */
void parse(const int32_t *ml, int n, int32_t *choice) {
    int64_t *cost = malloc(sizeof(int64_t) * (n + 1)); cost[n] = 0;
    for (int i = n - 1; i >= 0; i--) {
        int64_t best = 9 + cost[i+1]; int ch = 1;
        for (int l = 3; l <= ml[i]; l++) { int64_t c = 17 + cost[i+l]; if (c < best) { best = c; ch = l; } }
        cost[i] = best; choice[i] = ch;
    }
    free(cost);
}
