"""Item-page English overlay (TRIANGLE toggles a blue info box over the untouched page art).
usage: overlay.py <in SLPS_010.60> <out SLPS_010.60> <texts.json>
texts.json: {"<category>": ["text for item 0", "text for item 1", ...], ...}   (category = gp+3012 value)
The EXE image is extended so that our code/data load at EXT (free RAM, see NOTES_overlay.md)."""
import sys, struct, json, os
sys.path.insert(0, '/home/claude/scripts')
import exe_tool, safe

T0 = 0x80010200
EXT = 0x800E9000                  # start of our segment (RAM)
ST = EXT                          # state: +0 id, +4 on, +8 item, +12 cat
OBJ, DESC, BUF, WDESC = 0x801EF8C8, 0x8008027C, 0x8017F2F0, 0x8010ACEC
F = dict(strcpy=0x8003B5C8, memset=0x8003B5F8, tinit=0x8006EE60, tlay=0x8006E898, tfin=0x8006EED4,
         tclr1=0x8006E868, tclr2=0x8006EECC, tdraw=0x8006EF64, wopen=0x80072738, wrect=0x80072D3C,
         wcol=0x80072F28, wtxt=0x80073038, wbit=0x80073AD8, wclose=0x80072B44, wanim=0x80074F38, wdrawall=0x80073124)
WX, WY, WW = 258, 20, 244
MYDESC = 0x800E9F00
TXTPTR = 0x800E9F84
REOPEN_DELAY = int(os.environ.get('REOPEN_DELAY','40'))
TCOLS, TROWS, TEXX, TEXY = int(os.environ.get('TCOLS','20')), 11, int(os.environ.get('TEXX','984')), int(os.environ.get('TEXY','336'))
LAYER = int(os.environ.get('LAYER','1')); BLEND = int(os.environ.get('BLEND','8'))         # window rect (screen px); text is drawn at window + (8, 2)
PAD, CAT, ITEMTAB, RAWPAD = 3648, 3012, 0x8009EF38, 0x800BBC44
HOOK_IN, BACK_IN = 0x80026164, 0x8002616C     # item-page input case: "lw v0,3648(gp); nop"
HOOK_DRAW = 0x800255A4                        # Data File module per-frame "jal drawAllWindows"
START, START_BACK, BSS_LO, BSS_HI = 0x80018B9C, 0x80018BC0, 0x800BB930, 0x801F68F0

import os
LAYERTEST = bool(os.environ.get('LAYERTEST'))
MARK = [1] if os.environ.get('MARK') else []
REG = {n: i for i, n in enumerate(['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7',
                                   's0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra'])}

class Asm:
    def __init__(self, org): self.org = org; self.items = []; self.labels = {}
    def pc(self): return self.org + 4 * len(self.items)
    def L(self, name): self.labels[name] = self.pc()
    def w(self, fn): self.items.append(fn)
    def raw(self, word): self.items.append(lambda pc, L: word)
    # encoders
    def R(self, fn, rd='zero', rs='zero', rt='zero', sh=0):
        self.raw((REG[rs] << 21) | (REG[rt] << 16) | (REG[rd] << 11) | (sh << 6) | fn)
    def I(self, op, rt, rs, imm): self.raw((op << 26) | (REG[rs] << 21) | (REG[rt] << 16) | (imm & 0xffff))
    def nop(self): self.raw(0)
    def addu(self, d, s, t): self.R(0x21, d, s, t)
    def subu(self, d, s, t): self.R(0x23, d, s, t)
    def sll(self, d, t, sh): self.R(0x00, d, 'zero', t, sh)
    def sra(self, d, t, sh): self.R(0x03, d, 'zero', t, sh)
    def sltu(self, d, s, t): self.R(0x2b, d, s, t)
    def jr(self, s): self.R(0x08, 'zero', s)
    def move(self, d, s): self.addu(d, s, 'zero')
    def addiu(self, t, s, i): self.I(0x09, t, s, i)
    def andi(self, t, s, i): self.I(0x0c, t, s, i)
    def xori(self, t, s, i): self.I(0x0e, t, s, i)
    def lui(self, t, i): self.I(0x0f, t, 'zero', i)
    def lw(self, t, off, s): self.I(0x23, t, s, off); self.nop()   # R3000 load delay
    def lh(self, t, off, s): self.I(0x21, t, s, off); self.nop()
    def lbu(self, t, off, s): self.I(0x24, t, s, off); self.nop()
    def sw(self, t, off, s): self.I(0x2b, t, s, off)
    def sh(self, t, off, s): self.I(0x29, t, s, off)
    def li(self, t, v):
        v &= 0xffffffff
        if v < 0x8000 or v >= 0xffff8000: self.addiu(t, 'zero', v & 0xffff)
        else:
            lo = v & 0xffff; hi = ((v >> 16) + (1 if lo & 0x8000 else 0)) & 0xffff
            self.lui(t, hi); self.addiu(t, t, lo)
    def jal(self, a): self.raw((3 << 26) | ((a >> 2) & 0x3ffffff))
    def j(self, a): self.raw((2 << 26) | ((a >> 2) & 0x3ffffff))
    def jal_l(self, name): self.w(lambda pc, L: (3 << 26) | ((L[name] >> 2) & 0x3ffffff))
    def br(self, op, rs, rt, name):
        self.w(lambda pc, L: (op << 26) | (REG[rs] << 21) | (REG[rt] << 16) | (((L[name] - pc - 4) >> 2) & 0xffff))
    def beq(self, s, t, n): self.br(4, s, t, n)
    def bne(self, s, t, n): self.br(5, s, t, n)
    def b(self, n): self.br(4, 'zero', 'zero', n)
    def bltz(self, s, n): self.w(lambda pc, L: (1 << 26) | (REG[s] << 21) | (0 << 16) | (((L[n] - pc - 4) >> 2) & 0xffff))
    def bgez(self, s, n): self.w(lambda pc, L: (1 << 26) | (REG[s] << 21) | (1 << 16) | (((L[n] - pc - 4) >> 2) & 0xffff))
    def call(self, f):
        self.jal(F[f]); self.nop()
        if MARK: self.mark(MARK.pop(0) if False else self._mk())
    def _mk(self):
        self._n = getattr(self, '_n', 0) + 1; return self._n
    def mark(self, n):
        self.addiu('t9', 'zero', n); self.lui('t8', 0x800f); self.sw('t9', (0x800E9014 - 0x800F0000) & 0xffff, 't8')
    def build(self):
        return b''.join(struct.pack('<I', fn(self.org + 4 * i, self.labels)) for i, fn in enumerate(self.items))

def build(exe, texts):
    d = bytearray(exe)
    t_size = struct.unpack_from('<I', d, 0x1C)[0]
    assert len(d) == 0x800 + t_size
    a = Asm(EXT + 0x20)
    # ---------------- input hook: runs once per frame in the item page's input case
    a.L('stubA')
    if MARK: a.mark(100)
    a.addiu('sp', 'sp', -48); a.sw('ra', 40, 'sp'); a.sw('s0', 36, 'sp'); a.sw('s1', 32, 'sp'); a.sw('s2', 28, 'sp')
    a.li('s2', ST)
    a.lw('t0', CAT, 'gp'); a.sll('t1', 't0', 2); a.li('t2', ITEMTAB); a.addu('t2', 't2', 't1'); a.lw('s0', 0, 't2')
    cattab_fix = len(a.items); a.raw(0); a.raw(0)     # placeholder: lui/addiu t3 = CATTAB
    a.sll('t4', 't0', 3); a.addu('t3', 't3', 't4'); a.lw('t5', 0, 't3'); a.lw('t6', 4, 't3')
    a.move('s1', 'zero'); a.sltu('t7', 's0', 't5'); a.beq('t7', 'zero', 'A_pad'); a.nop()
    a.sll('t7', 's0', 2); a.addu('t6', 't6', 't7'); a.lw('s1', 0, 't6')
    a.L('A_pad')
    # raw pad word (bits: 0x10 TRIANGLE, 0x40 CROSS); edge = now & ~prev
    a.li('t8', RAWPAD); a.raw((0x25 << 26) | (REG['t8'] << 21) | (REG['t0'] << 16)); a.nop()   # lhu t0,0(t8)
    a.lw('t9', 16, 's2'); a.sw('t0', 16, 's2'); a.raw((REG['t9'] << 16) | (REG['t9'] << 11) | 0x27)  # nor t9,zero,t9
    a.raw((REG['t0'] << 21) | (REG['t9'] << 16) | (REG['t0'] << 11) | 0x24)               # and t0,t0,t9
    a.andi('t1', 't0', 0x40); a.beq('t1', 'zero', 'A_tri'); a.nop()
    a.jal_l('closebox'); a.nop()                                   # CROSS: leaving the page
    a.addiu('t1', 'zero', 1); a.sw('t1', 4, 's2'); a.b('A_done'); a.nop()
    a.L('A_tri')
    a.andi('t1', 't0', 0x10); a.beq('t1', 'zero', 'A_chk'); a.nop()
    if LAYERTEST:
        a.lw('t1', 28, 's2'); a.addiu('t1', 't1', 1); a.andi('t1', 't1', 7); a.sw('t1', 28, 's2')
        a.jal_l('closebox'); a.nop()
    else:
        a.lw('t1', 4, 's2'); a.xori('t1', 't1', 1); a.sw('t1', 4, 's2')   # TRIANGLE toggles
    a.L('A_chk')
    a.lw('t1', 0, 's2'); a.bltz('t1', 'A_open'); a.nop()
    a.lw('t2', 4, 's2'); a.beq('t2', 'zero', 'A_close'); a.nop()
    a.lw('t2', 8, 's2'); a.bne('t2', 's0', 'A_close'); a.nop()
    a.lw('t2', 12, 's2'); a.lw('t3', CAT, 'gp'); a.bne('t2', 't3', 'A_close'); a.nop()
    a.b('A_open'); a.nop()
    a.L('A_close'); a.jal_l('closebox'); a.nop()
    a.li('t0', 0x800E9F80); a.addiu('t1', 'zero', REOPEN_DELAY); a.sw('t1', 0, 't0')   # wait for the new page to load
    a.L('A_open')
    a.lw('t1', 4, 's2'); a.beq('t1', 'zero', 'A_done'); a.nop()
    a.lw('t1', 0, 's2'); a.bgez('t1', 'A_done'); a.nop()
    a.beq('s1', 'zero', 'A_done'); a.nop()
    a.move('a0', 's1'); a.jal_l('openbox'); a.nop()
    a.sw('s0', 8, 's2'); a.lw('t1', CAT, 'gp'); a.sw('t1', 12, 's2')
    a.L('A_done')
    a.lw('ra', 40, 'sp'); a.lw('s0', 36, 'sp'); a.lw('s1', 32, 'sp'); a.lw('s2', 28, 'sp'); a.addiu('sp', 'sp', 48)
    if MARK: a.mark(199)
    a.lw('v0', PAD, 'gp'); a.j(BACK_IN); a.nop()
    # ---------------- openbox(a0 = text)
    a.L('openbox')
    a.addiu('sp', 'sp', -40); a.sw('ra', 32, 'sp'); a.sw('s0', 28, 'sp'); a.sw('s1', 24, 'sp')
    if MARK: a.mark(200)
    a.move('s0', 'a0'); a.addiu('s1', 'zero', 1); a.move('t0', 's0')
    a.li('t9', TXTPTR); a.sw('s0', 0, 't9')
    a.L('O_cnt'); a.lbu('t1', 0, 't0'); a.beq('t1', 'zero', 'O_cnt_end'); a.addiu('t2', 't1', -10)
    a.bne('t2', 'zero', 'O_nx'); a.nop(); a.addiu('s1', 's1', 1)
    a.L('O_nx'); a.addiu('t0', 't0', 1); a.b('O_cnt'); a.nop()
    a.L('O_cnt_end')
    a.li('a0', BUF); a.move('a1', 's0'); a.call('strcpy')
    # private copy of the text descriptor (shared one belongs to the vehicle cards)
    a.li('t0', DESC); a.li('t1', MYDESC); a.addiu('t2', 'zero', 0x60)
    a.L('O_cp'); a.lw('t3', 0, 't0'); a.sw('t3', 0, 't1'); a.addiu('t0', 't0', 4); a.addiu('t1', 't1', 4)
    a.addiu('t2', 't2', -4); a.bne('t2', 'zero', 'O_cp'); a.nop()
    a.li('t0', MYDESC); a.addiu('t1', 'zero', WX + 8); a.sh('t1', 0x20, 't0'); a.addiu('t1', 'zero', WY + 2); a.sh('t1', 0x22, 't0')
    a.addiu('t1', 'zero', TCOLS); a.sh('t1', 0x24, 't0'); a.sh('s1', 0x26, 't0')   # rows = actual line count
    a.addiu('t1', 'zero', TEXX); a.sh('t1', 0x28, 't0'); a.addiu('t1', 'zero', TEXY); a.sh('t1', 0x2A, 't0')
    a.li('a0', OBJ); a.li('a1', MYDESC); a.call('tinit')
    a.li('a0', OBJ); a.call('tlay')
    a.li('a0', OBJ); a.call('tfin')
    a.li('a0', WDESC); a.move('a1', 'zero'); a.addiu('a2', 'zero', 132); a.call('memset')
    a.li('t0', WDESC); a.addiu('t1', 'zero', 16); a.sh('t1', 8, 't0'); a.addiu('t1', 'zero', 4); a.sh('t1', 10, 't0')
    a.li('a0', WDESC); a.call('wopen')
    a.sll('v0', 'v0', 16); a.sra('v0', 'v0', 16); a.li('t0', ST); a.sw('v0', 0, 't0')
    # window draw layer (slot+2) from ST+28
    a.sll('t1', 'v0', 7); a.sll('t2', 'v0', 2); a.addu('t1', 't1', 't2'); a.li('t2', 0x8017EED0); a.addu('t1', 't1', 't2')
    a.lw('t3', 28, 't0'); a.sh('t3', 2, 't1')
    a.sll('t1', 's1', 4); a.sll('t2', 's1', 1); a.subu('t1', 't1', 't2'); a.addiu('t1', 't1', 8); a.sw('t1', 16, 'sp')
    a.move('a0', 'v0'); a.addiu('a1', 'zero', WX); a.addiu('a2', 'zero', WY); a.addiu('a3', 'zero', WW); a.call('wrect')
    a.li('t0', ST); a.lw('a0', 0, 't0'); a.move('a1', 'zero'); a.move('a2', 'zero'); a.addiu('a3', 'zero', 255)
    a.addiu('t1', 'zero', BLEND); a.sw('t1', 16, 'sp'); a.call('wcol')
    a.li('t0', ST); a.lw('a0', 0, 't0'); a.addiu('a1', 'zero', 191); a.addiu('a2', 'zero', 191); a.addiu('a3', 'zero', 191); a.call('wtxt')
    if os.environ.get('TRANS'):
        a.li('t0', ST); a.lw('a0', 0, 't0'); a.addiu('a1', 'zero', 1); a.call('wbit')
    a.lw('ra', 32, 'sp'); a.lw('s0', 28, 'sp'); a.lw('s1', 24, 'sp'); a.addiu('sp', 'sp', 40); a.jr('ra'); a.nop()
    # ---------------- closebox()
    a.L('closebox')
    a.addiu('sp', 'sp', -24); a.sw('ra', 16, 'sp')
    if MARK: a.mark(300)
    a.li('t0', ST); a.lw('a0', 0, 't0'); a.bltz('a0', 'C_end'); a.nop()
    a.call('wclose')
    a.li('t0', ST); a.lw('a0', 0, 't0'); a.move('a1', 'zero'); a.call('wbit')
    a.li('a0', OBJ); a.call('tclr1')
    a.li('a0', OBJ); a.call('tclr2')
    a.li('t0', ST); a.addiu('t1', 'zero', -1); a.sw('t1', 0, 't0')
    a.L('C_end'); a.lw('ra', 16, 'sp'); a.addiu('sp', 'sp', 24); a.jr('ra'); a.nop()
    # ---------------- draw hook: replaces "jal drawAllWindows" in the Data File frame
    a.L('stubB')
    a.addiu('sp', 'sp', -24); a.sw('ra', 16, 'sp')
    a.li('t0', ST); a.lw('t1', 24, 't0'); a.addiu('t1', 't1', 1); a.sw('t1', 24, 't0')   # frame counter
    a.li('t0', ST); a.lw('a0', 0, 't0'); a.bltz('a0', 'B_end'); a.nop()
    a.call('wanim'); a.addiu('t1', 'zero', 1); a.beq('v0', 't1', 'B_end'); a.nop()
    a.li('a0', OBJ); a.call('tdraw')
    a.L('B_end'); a.lw('ra', 16, 'sp'); a.addiu('sp', 'sp', 24); a.j(F['wdrawall']); a.nop()
    # ---------------- stubC: scheduler hook just before DrawOTag (replaces 'jal 0x8003cd70' at 0x80059808)
    a.L('stubC')
    a.addiu('sp', 'sp', -32); a.sw('ra', 24, 'sp'); a.sw('a0', 20, 'sp'); a.sw('s0', 16, 'sp')
    a.li('t0', ST); a.lw('t1', 24, 't0'); a.addiu('t1', 't1', 1); a.sw('t1', 24, 't0')   # frame counter
    a.lw('a0', 0, 't0'); a.bltz('a0', 'C2_end'); a.nop()
    a.sll('t1', 'a0', 7); a.sll('t2', 'a0', 2); a.addu('t1', 't1', 't2'); a.li('t2', 0x8017EED0); a.addu('s0', 't1', 't2')
    # after a page change, don't draw for REOPEN_DELAY frames (page load passes through the text VRAM)
    a.li('t0', 0x800E9F80); a.lw('t1', 0, 't0'); a.beq('t1', 'zero', 'C2_win'); a.nop()
    a.addiu('t1', 't1', -1); a.sw('t1', 0, 't0'); a.b('C2_end'); a.nop()
    a.L('C2_win')
    a.move('a0', 's0'); a.jal(0x80074E10); a.nop()
    a.beq('v0', 'zero', 'C2_end'); a.nop()          # window not drawn this frame -> no text either
    a.move('a0', 's0'); a.lh('a1', 4, 's0'); a.jal(0x80074824); a.nop()
    a.move('a0', 's0'); a.jal(0x800731B8); a.nop()
    a.L('C2_txt')
    a.li('t0', ST); a.lw('a0', 0, 't0'); a.call('wanim'); a.addiu('t1', 'zero', 1); a.beq('v0', 't1', 'C2_end'); a.nop()
    a.li('a0', OBJ); a.call('tdraw')
    a.L('C2_end')
    a.lw('ra', 24, 'sp'); a.lw('a0', 20, 'sp'); a.lw('s0', 16, 'sp'); a.addiu('sp', 'sp', 32)
    a.j(0x8003CD70); a.nop()
    # ---------------- startup: BSS clear (0x800BB930..0x801F68F0) must skip our segment
    a.L('clr')
    a.li('v0', BSS_LO); a.li('v1', EXT)
    a.L('CL1'); a.raw(0xAC400000)                     # sw zero,0(v0)
    a.addiu('v0', 'v0', 4); a.sltu('at', 'v0', 'v1'); a.bne('at', 'zero', 'CL1'); a.nop()
    clr_fix = len(a.items); a.raw(0); a.raw(0)          # placeholder: lui/addiu v0 = segment end
    a.li('v1', BSS_HI)
    a.L('CL2'); a.raw(0xAC400000)
    a.addiu('v0', 'v0', 4); a.sltu('at', 'v0', 'v1'); a.bne('at', 'zero', 'CL2'); a.nop()
    a.j(START_BACK); a.nop()
    code_end = a.pc()
    # ---------------- data: category table + pointer arrays + strings
    cats = {int(k): v for k, v in texts.items()}
    ncat = 8
    cattab = (code_end + 15) & ~15
    pos = cattab + ncat * 8
    blob = bytearray(); arrays = {}; strings = []
    for c in range(ncat):
        lst = cats.get(c, [])
        arrays[c] = pos + len(blob); blob += b'\0' * (4 * len(lst))
    strpos = {}
    for c in range(ncat):
        for i, s in enumerate(cats.get(c, [])):
            if not s: continue
            enc = exe_tool.encode(safe.sanitize(s.replace('\n', '\\n'))) + b'\0'
            strpos[(c, i)] = pos + len(blob); blob += enc
            while len(blob) % 4: blob += b'\0'
    for (c, i), sp in strpos.items():
        struct.pack_into('<I', blob, arrays[c] - pos + 4 * i, sp)
    tab = b''.join(struct.pack('<II', len(cats.get(c, [])), arrays[c]) for c in range(ncat))
    # patch CATTAB address into stubA's li
    hi = ((cattab >> 16) + (1 if cattab & 0x8000 else 0)) & 0xffff; lo = cattab & 0xffff
    a.items[cattab_fix] = (lambda h: (lambda pc, L: (0x0f << 26) | (REG['t3'] << 16) | h))(hi)
    a.items[cattab_fix + 1] = (lambda l: (lambda pc, L: (0x09 << 26) | (REG['t3'] << 21) | (REG['t3'] << 16) | l))(lo)
    seg_end = (cattab + len(tab) + len(blob) + 3) & ~3
    shi = ((seg_end >> 16) + (1 if seg_end & 0x8000 else 0)) & 0xffff; slo = seg_end & 0xffff
    a.items[clr_fix] = (lambda h: (lambda pc, L: (0x0f << 26) | (REG['v0'] << 16) | h))(shi)
    a.items[clr_fix + 1] = (lambda l: (lambda pc, L: (0x09 << 26) | (REG['v0'] << 21) | (REG['v0'] << 16) | l))(slo)
    code = a.build()
    seg = bytearray(struct.pack('<iiiiiiii', -1, 1, -1, -1, 0, 0, 0, LAYER)) + code
    seg += b'\0' * (cattab - (EXT + len(seg))) + tab + blob
    # ---------------- splice into the EXE
    img = d[0x800:]
    need = EXT - T0
    img += b'\0' * (need - len(img)) + seg
    img += b'\0' * ((-len(img)) % 2048)
    out = bytearray(d[:0x800]) + img
    struct.pack_into('<I', out, 0x1C, len(img))
    def put(addr, word): struct.pack_into('<I', out, addr - T0 + 0x800, word)
    pass
    if not os.environ.get('NO_IN'):
        put(HOOK_IN, (2 << 26) | ((a.labels['stubA'] >> 2) & 0x3ffffff)); put(HOOK_IN + 4, 0)
    if os.environ.get('OLD_DRAW'):
        put(HOOK_DRAW, (3 << 26) | ((a.labels['stubB'] >> 2) & 0x3ffffff))
    elif not os.environ.get('NO_DRAW'):
        put(0x80059808, (3 << 26) | ((a.labels['stubC'] >> 2) & 0x3ffffff))   # delay slot keeps 'addiu a0,zero,1'
    put(START, (2 << 26) | ((a.labels['clr'] >> 2) & 0x3ffffff)); put(START + 4, 0)
    print(f'segment {EXT:#x}..{EXT + len(seg):#x} ({len(seg)} bytes), code {len(code)} bytes, text blob {len(blob)} bytes,'
          f' EXE {len(d)} -> {len(out)} bytes')
    return bytes(out)

if __name__ == '__main__':
    src, dst, tj = sys.argv[1:4]
    out = build(open(src, 'rb').read(), json.load(open(tj, encoding='utf-8')))
    open(dst, 'wb').write(out)
