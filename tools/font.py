import struct, sys
sys.path.insert(0, '/home/claude/scripts'); import labelenc as L
A2O = lambda a: a - 0x80010200 + 0x800
NBASE = A2O(0x8007639C); NTAB = A2O(0x800757D0)
def narrow_list(d): return [struct.unpack_from('<H', d, NTAB + 2 * i)[0] for i in range(134)]
def glyph_off(d, ch):
    """file offset of the narrow bitmap for a full-width char ch"""
    code = int.from_bytes(ch.encode('cp932'), 'big')
    n = L.narrow_index(code); return NBASE + narrow_list(d).index(n) * 16
def get(d, ch): o = glyph_off(d, ch); return [d[o + r] for r in range(16)]
def show(rows_list):
    for r in range(13): print(' '.join(''.join('#' if g[r] >> (7 - k) & 1 else '.' for k in range(8)) for g in rows_list))
def parse(lines):
    rows = [0] * 16
    for i, ln in enumerate(lines): rows[i] = int(ln.replace('#', '1').replace('.', '0'), 2)
    return rows
