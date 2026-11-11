"""Code + font patches for the label/INFORMATION renderer of SLPS_010.60.

1. Binary search at 0x800199F4 rewritten so a missing glyph returns index 0 instead of looping forever.
2. Hook at 0x80019C84 (single-byte glyph lookup): ASCII 0x21-0x7E is translated through a table into
   the full-width code whose *narrow* glyph is drawn, so plain ASCII English renders in labels/text.
3. Ten new narrow glyphs drawn over unused narrow katakana: J Q U Z j q ' " ! ?
"""
import struct, sys
sys.path.insert(0, '/home/claude/scripts')
import font as F

T = 0x80010200
A2O = lambda a: a - T + 0x800
O2A = lambda o: T + o - 0x800

# ---------- tiny MIPS assembler ----------
R = {n: i for i, n in enumerate(['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7',
                                  's0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra'])}
def rtype(fn, rd='zero', rs='zero', rt='zero', sh=0): return (R[rs] << 21) | (R[rt] << 16) | (R[rd] << 11) | (sh << 6) | fn
def itype(op, rt, rs, imm): return (op << 26) | (R[rs] << 21) | (R[rt] << 16) | (imm & 0xffff)
def addu(rd, rs, rt): return rtype(0x21, rd, rs, rt)
def slt(rd, rs, rt): return rtype(0x2a, rd, rs, rt)
def sltu(rd, rs, rt): return rtype(0x2b, rd, rs, rt)
def sll(rd, rt, sh): return rtype(0x00, rd, 'zero', rt, sh)
def sra(rd, rt, sh): return rtype(0x03, rd, 'zero', rt, sh)
def jr(rs): return rtype(0x08, 'zero', rs)
def addiu(rt, rs, imm): return itype(0x09, rt, rs, imm)
def sltiu(rt, rs, imm): return itype(0x0b, rt, rs, imm)
def andi(rt, rs, imm): return itype(0x0c, rt, rs, imm)
def lui(rt, imm): return itype(0x0f, rt, 'zero', imm)
def lhu(rt, off, rs): return itype(0x25, rt, rs, off)
def beq(rs, rt, off): return itype(0x04, rt, rs, off)
def bne(rs, rt, off): return itype(0x05, rt, rs, off)
def j(addr): return (0x02 << 26) | ((addr >> 2) & 0x3ffffff)
NOP = 0
def hi_lo(addr):
    lo = addr & 0xffff; hi = (addr >> 16) + (1 if lo & 0x8000 else 0)
    return hi & 0xffff, lo

def asm(lines, labels):
    """lines: list of (label or None, callable(pc)->word). Branch offsets resolved via labels dict."""
    return lines

# ---------- glyphs ----------
GLYPHS = {
 'ァ': ('J', ["........","....#...","....#...","....#...","....#...","....#...","....#...","....#...","....#...","#...#...","#...#...",".###...."]),
 'ィ': ('Q', ["........",".####...","#....#..","#....#..","#....#..","#....#..","#....#..","#....#..","#....#..","#..#.#..","#...#...",".###.#.."]),
 'ェ': ('U', ["........","#....#..","#....#..","#....#..","#....#..","#....#..","#....#..","#....#..","#....#..","#....#..","#....#..",".####..."]),
 'ォ': ('Z', ["........","######..",".....#..","....#...","....#...","...#....","...#....","..#.....","..#.....",".#......","#.......","######.."]),
 'ャ': ('j', ["........","....#...","....#...","........","....#...","....#...","....#...","....#...","....#...","....#...","....#...","#...#...",".###...."]),
 'ョ': ('q', ["........","........","........","........","..####..",".#...#..",".#...#..",".#...#..",".#...#..",".#...#..","..####..",".....#..",".....#.."]),
 'ッ': ("'", ["........","..##....","..##....","...#....","..#.....","........","........","........","........","........","........","........"]),
 'ヘ': ('"', ["........",".#..#...",".#..#...",".#..#...","........","........","........","........","........","........","........","........"]),
 'ヒ': ('!', ["........","...#....","...#....","...#....","...#....","...#....","...#....","...#....","...#....","........","...#....","...#...."]),
 'ホ': ('?', ["........",".####...","#....#..",".....#..","....#...","...#....","...#....","...#....","...#....","........","...#....","...#...."]),
}

def ascii_table():
    tbl = {}
    for c in range(0x21, 0x7f):
        ch = chr(c)
        tbl[c] = ch
    fw = {}
    for c, ch in tbl.items():
        if 0x21 <= c <= 0x7e: fw[c] = chr(c + 0xfee0)
    punct = {'.': '．', ',': '，', '-': '－', ':': '：', ';': '；', '(': '（', ')': '）', '/': '／', '%': '％', '=': '＝'}
    for k, v in punct.items(): fw[ord(k)] = v
    for kana, (asc, _) in GLYPHS.items(): fw[ord(asc)] = kana
    return {c: int.from_bytes(fw[c].encode('cp932'), 'big') for c in fw}

SUPPORTED = None
def supported(d):
    """ASCII chars that will render (narrow glyph exists after patching)."""
    import labelenc as L
    ns = set(F.narrow_list(d)); ok = set(' ')
    for c, code in ascii_table().items():
        n = L.narrow_index(code)
        if n in ns: ok.add(chr(c))
    return ok

def apply(d, cave):
    """d: bytearray of the exe. cave: file offset of >= 256 free bytes (4-aligned)."""
    # 3. glyphs
    for kana, (_, rows) in GLYPHS.items():
        o = F.glyph_off(bytes(d), kana); g = F.parse(rows)
        d[o:o+16] = bytes(g)
    # 1. safe binary search at 0x800199F4 (30 instruction slots)
    code = [
        andi('a0', 'a0', 0xffff),        # 0
        addu('t0', 'zero', 'zero'),      # 1
        slt('v0', 'a2', 't0'),           # 2 loop
        bne('v0', 'zero', 20 - 4),       # 3 -> 20 nf
        addu('a3', 't0', 'a2'),          # 4 delay
        sra('a3', 'a3', 1),              # 5
        sll('v1', 'a3', 1),              # 6
        addu('v1', 'v1', 'a1'),          # 7
        lhu('v1', 0, 'v1'),              # 8
        NOP,                             # 9
        beq('v1', 'a0', 18 - 11),        # 10 -> 18 found
        sltu('v0', 'a0', 'v1'),          # 11 delay
        beq('v0', 'zero', 16 - 13),      # 12 -> 16 gt
        NOP,                             # 13
        beq('zero', 'zero', 2 - 15),     # 14 -> loop
        addiu('a2', 'a3', -1),           # 15 delay
        beq('zero', 'zero', 2 - 17),     # 16 gt -> loop
        addiu('t0', 'a3', 1),            # 17 delay
        jr('ra'),                        # 18 found
        addu('v0', 'a3', 'zero'),        # 19
        jr('ra'),                        # 20 nf
        addu('v0', 'zero', 'zero'),      # 21
    ] + [NOP] * 8
    o = A2O(0x800199F4)
    for i, w in enumerate(code): struct.pack_into('<I', d, o + 4 * i, w)
    # 2. ASCII table + hook
    tbl_off = cave; tbl_addr = O2A(tbl_off)                # 94 entries for 0x21..0x7E
    for c, v in ascii_table().items(): struct.pack_into('<H', d, tbl_off + 2 * (c - 0x21), v)
    stub_off = tbl_off + 192; stub = O2A(stub_off)
    hi, lo = hi_lo(tbl_addr - 0x42)
    s = [
        addu('s0', 'a0', 'zero'),        # 0 original instruction
        andi('t9', 's0', 0xffff),        # 1
        sltiu('at', 't9', 0x21),         # 2
        bne('at', 'zero', 10 - 4),       # 3 -> 10 ret
        sltiu('at', 't9', 0x7f),         # 4 delay
        beq('at', 'zero', 10 - 6),       # 5 -> 10 ret
        sll('t9', 't9', 1),              # 6 delay
        lui('at', hi),                   # 7
        addu('at', 'at', 't9'),          # 8
        lhu('s0', lo, 'at'),             # 9
        j(0x80019C8C),                   # 10 ret
        NOP,                             # 11
    ]
    for i, w in enumerate(s): struct.pack_into('<I', d, stub_off + 4 * i, w)
    struct.pack_into('<I', d, A2O(0x80019C84), j(stub))   # delay slot keeps 'addu v1,zero,zero'
    return stub_off + 4 * len(s) - cave                    # bytes used
CAVE_SIZE = 192 + 48
