"""Greedy substring dictionary for the overlay text: up to N tokens, each a byte string without NUL or token bytes."""
from collections import Counter
def build(strings, n, minlen=3, maxlen=14, tok0=0x90):
    data = [bytearray(s) for s in strings]
    toks = []
    for k in range(n):
        cnt = Counter()
        for s in data:
            L = len(s)
            for i in range(L):
                for l in range(minlen, maxlen + 1):
                    if i + l > L: break
                    sub = bytes(s[i:i + l])
                    if 0 in sub or max(sub) >= tok0: break
                    cnt[sub] += 1
        best = None; gain = 0
        for sub, c in cnt.items():
            g = c * (len(sub) - 1) - (len(sub) + 3)
            if g > gain: gain, best = g, sub
        if not best: break
        code = tok0 + k; toks.append(best)
        data = [bytearray(bytes(s).replace(best, bytes([code]))) for s in data]
    return toks, [bytes(s) for s in data]
