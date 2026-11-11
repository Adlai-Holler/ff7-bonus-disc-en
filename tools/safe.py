import re
SAFE = set(" ,.:()/-0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz")
SUB = {"'": "’", '"': None, ';': ',', '!': '！', '?': '？', '&': '＆', '=': '＝', '+': '＋', '%': '％', '*': '＊', '#': '＃', '~': '～', '<': '＜', '>': '＞', '[': '【', ']': '】'}
def sanitize(s):
    out = []; q = 0; i = 0
    while i < len(s):
        m = re.match(r'\{~f..\}|\{..\}|\\n', s[i:])
        if m: out.append(m.group()); i += len(m.group()); continue
        c = s[i]
        if c == '"': out.append('“' if q == 0 else '”'); q ^= 1
        elif c in SUB: out.append(SUB[c])
        elif ord(c) < 0x80 and c not in SAFE: raise ValueError(f'unsafe char {c!r} in {s!r}')
        else: out.append(c)
        i += 1
    return ''.join(out)
