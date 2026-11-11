"""Encoder for the hotspot/map label renderer (font subset discovered in SLPS_010.60).
Narrow glyph = '@' + full-width char (3 bytes); wide glyph = full-width char (2 bytes)."""
import struct
EXE = '/mnt/user-data/uploads/ff7pg/ff7pg_unpacked_base/SLPS_010.60'
_d = open(EXE, 'rb').read()
def _a2o(a): return a - 0x80010200 + 0x800
def _table(a):
    o = _a2o(a); v = []
    while True:
        x = struct.unpack_from('<H', _d, o)[0]
        if v and x <= v[-1]: return set(v)
        v.append(x); o += 2
WIDE = _table(0x800758DC)
NARROW = _table(0x800757D0)
PUNCT = {}
for k in range(0, 208, 4):
    a, b = struct.unpack_from('<HH', _d, _a2o(0x80075648) + k); PUNCT[a] = b

def narrow_index(code):
    if code in PUNCT and not (0x824f <= code <= 0x8396): return PUNCT[code]
    if 0x824f <= code <= 0x8396:
        base = max(k for k in PUNCT if k <= code and k >= 0x824f)
        return PUNCT[base] + code - base
    return None

def fw(c):
    if c == ' ': return 0x8140
    return int.from_bytes(chr(ord(c) + 0xfee0).encode('cp932'), 'big') if 0x21 <= ord(c) <= 0x7e else None

PUNCT_FW = {'.': '．', ',': '，', '-': '－', ':': '：', '(': '（', ')': '）', '/': '／', '!': '！', '?': '？', '&': '＆'}

def encode_label(s):
    """returns the label as a str using only renderer-safe characters"""
    out = []; i = 0
    while i < len(s):
        if s.startswith('\\n', i): out.append('\\n'); i += 2; continue
        c = s[i]; i += 1
        if c == ' ': out.append(' '); continue
        if c in "'’\"“”": continue
        if ord(c) >= 0x3000 and c not in '’“”':   # already Japanese/full-width: keep if drawable
            out.append(c); continue
        f = PUNCT_FW.get(c) or (chr(ord(c) + 0xfee0) if 0x21 <= ord(c) <= 0x7e else None)
        if f is None: raise ValueError(f'no glyph for {c!r} in {s!r}')
        code = int.from_bytes(f.encode('cp932'), 'big')
        n = narrow_index(code)
        if n is not None and n in NARROW: out.append('@' + f)
        elif code in WIDE: out.append(f)
        else: raise ValueError(f'no glyph for {c!r} in {s!r}')
    return ''.join(out)

if __name__ == '__main__':
    import sys
    for t in sys.argv[1:]: print(t, '->', encode_label(t), len(encode_label(t).encode('cp932')))
    missing = [c for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
               if not (narrow_index(int.from_bytes(chr(ord(c)+0xfee0).encode('cp932'),'big')) in NARROW)]
    print('no narrow glyph:', missing)


import textwrap
WIDE_PUNCT = {'.': '．', ',': '，', '-': '－', ':': '：', '(': '（', ')': '）', '/': '／', '!': '！', '?': '？',
              '&': '＆', '=': '＝', '*': '★', '~': '～'}
def _units(t): return sum(0.5 if c == ' ' else 1 for c in t)

def _wrap_units(text, width):
    words = text.split(' '); lines = []; cur = ''
    for w in words:
        cand = (cur + ' ' + w) if cur else w
        if _units(cand) <= width or not cur: cur = cand
        else: lines.append(cur); cur = w
    lines.append(cur)
    return lines

def encode_wide(s, width=14):
    """All-caps wide label. Returns renderer-safe str (lines <= width display units)."""
    import re
    s = s.replace('\\\\n', '\\n')
    s = re.sub(r'Materia:', 'Mat.:', s) if _units(s.split('\\n')[0].replace('\\\\n','')) > width else s
    lines = []
    for raw in s.split('\\n'):
        raw = ''.join(c for c in raw if c not in "'’\"“”")
        lead = len(raw) - len(raw.lstrip(' '))
        body = _wrap_units(raw.strip(), width - min(lead, 2) * 0.5) or ['']
        body[0] = ' ' * min(lead, 2) + body[0]
        lines += body
    out = []
    for ln in lines:
        o = []
        for c in ln.upper():
            if c == ' ': o.append(' '); continue
            if ord(c) >= 0x3000: o.append(c); continue
            f = WIDE_PUNCT.get(c) or (chr(ord(c) + 0xfee0) if 0x21 <= ord(c) <= 0x7e else None)
            code = int.from_bytes(f.encode('cp932'), 'big') if f else None
            if code not in WIDE: raise ValueError(f'no wide glyph for {c!r} in {s!r}')
            o.append(f)
        out.append(''.join(o))
    return '\\n'.join(out)

def is_label(o):
    return (0x2504 <= o < 0x7540) or (0x79aac <= o < 0x8f000) or (0xab000 <= o < 0xabd50)


# ---- after asmpatch: plain ASCII renders in narrow glyphs ----
ASCII_OK = set(" ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,-:;()/%=\'\"!?")
ASCII_SUB = {'’': "'", '‘': "'", '“': '"', '”': '"', '&': 'and', '+': '+', '…': '...', '—': '-', '–': '-', '°': ' deg', '*': '', '[': '(', ']': ')', '~': '-'}
def encode_ascii(s, width=26):
    s = s.replace('\\\\n', '\\n')
    out = []
    for raw in s.split('\\n'):
        import unicodedata
        t = ''.join(ASCII_SUB.get(c, unicodedata.normalize('NFKC', c) if 0xff01 <= ord(c) <= 0xff5e else c) for c in raw)
        t = t.replace('【', '(').replace('】', ')')
        bad = [c for c in t if c not in ASCII_OK]
        if bad: raise ValueError(f'no glyph for {bad!r} in {s!r}')
        lead = len(t) - len(t.lstrip(' '))
        words = t.strip().split(' '); lines = []; cur = ''
        for w in words:
            cand = (cur + ' ' + w) if cur else w
            if len(cand) + min(lead, 2) <= width or not cur: cur = cand
            else: lines.append(cur); cur = w
        lines.append(cur)
        lines[0] = ' ' * min(lead, 2) + lines[0]
        out += lines
    return '\\n'.join(out)

def is_text(o):
    return 0x75000 <= o < 0x79aac
