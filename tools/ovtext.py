"""Overlay text encoding + layout preview.
Markup: {g} gold, {w} white, {c} cyan, \t = tab to label column, \n newline, ' -> ’ glyph, △ ○ × □ symbols."""
import re, ovfont
CTRL = {'{w}': 2, '{g}': 1, '{c}': 3}
INDENT = 9
SYMREV = {v: k for k, v in ovfont.SYM.items()}
def encode(s):
    s = s.replace("'", '’')
    out = bytearray(); i = 0
    while i < len(s):
        m = re.match(r'\{[wgc]\}', s[i:])
        if m: out.append(CTRL[m.group()]); i += 3; continue
        ch = s[i]; i += 1
        if ch == '\n': out.append(10)
        elif ch == '\t': out.append(9)
        elif ch == '\u00a0': out.append(32)          # no-break space
        elif ch == '\v': out.append(4)
        elif ch in SYMREV: out.append(SYMREV[ch])
        elif 32 <= ord(ch) < 127: out.append(ord(ch))
        else: raise ValueError('no glyph for %r in %r' % (ch, s))
    return bytes(out) + b'\0'

def layout(b, table, x0, y0, tab, lh):
    """yields (code, x, y, palette) like the MIPS loop does; returns width/height too"""
    x, y, pal = x0, y0, 0; out = []; maxx = x0
    for c in b:
        if c == 0: break
        if c == 10: x = x0; y += lh; continue
        if c == 9: x = x0 + tab; continue
        if c == 4: x = x0 + INDENT; continue
        if c in (1, 2, 3): pal = {2: 0, 1: 1, 3: 2}[c]; continue
        u, v, w, adv = table[c][:4]
        if w: out.append((c, x, y, pal))
        x += adv; maxx = max(maxx, x)
    return out, maxx - x0, y - y0 + lh

def wrap(s, table, maxw, tab):
    """word-wrap each line to maxw px; continuation of a tab line restarts at the tab column, of a bullet line at INDENT"""
    def width(t): return layout(encode(t)[:-1] + b'\0', table, 0, 0, tab, 12)[1]
    out = []
    for line in s.split('\n'):
        if width(line) <= maxw: out.append(line); continue
        cont = '\t' if '\t' in line else '\v' if line.lstrip('{wgc}').startswith('•') or '•' in line[:6] else ''
        words = line.split(' '); cur = words[0]
        for w in words[1:]:
            if width(cur + ' ' + w) <= maxw: cur += ' ' + w
            else:
                out.append(cur); cur = cont + w
        out.append(cur)
    return '\n'.join(out)
