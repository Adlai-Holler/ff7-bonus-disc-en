"""Item-page English overlay v2: own renderer (no game window/text system).
usage: overlay2.py <in SLPS_010.60> <out SLPS_010.60> <texts.json>
- Shrinks the game's two primitive buffers (0x21000 -> PRIMSZ each) so RAM 0x800C6218+2*PRIMSZ .. 0x80108218 is ours.
- stubA (item-page input case): picks the text for (category, item), TRIANGLE toggles, stamps 'alive'.
- stubC (scheduler, just before DrawOTag): if the item page ran this frame, uploads font+CLUT (LoadImage) and adds
  box (POLY_G4 + border TILEs), a TPAGE and glyph SPRTs into OT bucket LAYER of the frame being drawn.
Text markup (texts.json): {g} gold {w} white {c} cyan, \\t = tab column, \\n newline."""
import sys, struct, json, os
sys.path.insert(0, '/home/claude/scripts')
import ovfont, ovtext

T0 = 0x80010200
PRIMSZ = int(os.environ.get('PRIMSZ', '0x18000'), 0)
PRIM0 = 0x800C6218
EXT = (PRIM0 + 2 * PRIMSZ + 0x7ff) & ~0x7ff          # our segment
LIMIT = 0x80108218
FX, FY = int(os.environ.get('FX', '512'), 0), int(os.environ.get('FY', '240'), 0)     # font strips VRAM (free rows in page-screen VRAM)
CX, CY = int(os.environ.get('CX', '512'), 0), int(os.environ.get('CY', '496'), 0)     # 3 CLUTs at CX, CX+16, CX+32
LAYER = int(os.environ.get('LAYER', '1'))
WX, WY, WW = 268, 28, 184
WX2, WY2, WW2 = 28, 28, 456     # wide box for field close-up / instructions tips (text set 5), under the name box
PADX, PADY, LH, TABX = 6, 5, 13, 62
INK_TOP, INK_BOT, BASE_BOT = 1, 15, 12      # first/last inked row of a glyph cell (cap top / descender+shadow)
TABY, TABH = 8, 19
NX, NY, NW, NH = 38, 28, 196, 24      # name box over the Japanese title (left page)
# book key: (total pages, first sub-list count or 0 = any). 0 weapons, 1 armor, 2 accessories, 4 other
BOOKIDX = {c: int(v) for c, v in zip((0, 1, 2, 3, 4), os.environ.get('BOOKIDX', '0,1,2,3,4').split(','))}
BOOKIDX[5] = 5      # field close-up tooltips (keyed by hotspot label pointer, see TIPKEYS)   # text set -> game book index (gp+3016)
TOK0 = 0x90         # bytes >= TOK0 are dictionary tokens
MAXBOT = 232        # lowest screen row the box may reach
LOADIMAGE, ADDR_FRAME, OTDESC, PRIMPTR, SCROFF = 0x8003D4F4, 0x800BB868, 0x801EF388, 0x8017F1E8, 0x801EC528
PAD, CAT, ITEMTAB, RAWPAD = 3648, 3012, 0x8009EF38, 0x800BBC44
TOP, COUNTS = 3016, 0x8009EF60     # book (Weapons/Armor/...) and per-sub-list item counts
HOOK_IN, BACK_IN = 0x80026134, 0x80026140
SHOOK2, SBACK2 = 0x80027C08, 0x80027C10
SHOOK, SBACK = 0x800282F8, 0x80028300   # shop LIST page: same 'lui v0; lhu v0,pad' before its CROSS test
FHOOK, FBACK = 0x80026BB8, 0x80026BC0   # field item page: 'lui v0,0x800c; lhu v0,-17340(v0)' before the CROSS test
BOOKSEL = 0x800BBC2C
HOOK_SCHED, SCHED_FN = 0x80059808, 0x8003CD70
START, START_BACK, BSS_LO, BSS_HI = 0x80018B9C, 0x80018BC0, 0x800BB930, 0x801F68F0
PRIMSZ_PATCH = 0x800195A8
GH = ovfont.GH + 1

REG = {n: i for i, n in enumerate(['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7',
                                   's0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra'])}
class Asm:
    def __init__(self, org): self.org = org; self.items = []; self.labels = {}
    def pc(self): return self.org + 4 * len(self.items)
    def L(self, n): assert n not in self.labels, n; self.labels[n] = self.pc()
    def raw(self, w): self.items.append(lambda pc, L, w=w: w)
    def R(self, fn, rd='zero', rs='zero', rt='zero', sh=0):
        self.raw((REG[rs] << 21) | (REG[rt] << 16) | (REG[rd] << 11) | (sh << 6) | fn)
    def I(self, op, rt, rs, imm): self.raw((op << 26) | (REG[rs] << 21) | (REG[rt] << 16) | (imm & 0xffff))
    def nop(self): self.raw(0)
    def addu(self, d, s, t): self.R(0x21, d, s, t)
    def subu(self, d, s, t): self.R(0x23, d, s, t)
    def or_(self, d, s, t): self.R(0x25, d, s, t)
    def and_(self, d, s, t): self.R(0x24, d, s, t)
    def nor(self, d, s, t): self.R(0x27, d, s, t)
    def sltu(self, d, s, t): self.R(0x2b, d, s, t)
    def sll(self, d, t, sh): self.R(0x00, d, 'zero', t, sh)
    def srl(self, d, t, sh): self.R(0x02, d, 'zero', t, sh)
    def sra(self, d, t, sh): self.R(0x03, d, 'zero', t, sh)
    def slt(self, d, s, t): self.R(0x2a, d, s, t)
    def lb(self, t, o, s): self.I(0x20, t, s, o); self.nop()
    def jr(self, s): self.R(0x08, 'zero', s)
    def move(self, d, s): self.addu(d, s, 'zero')
    def addiu(self, t, s, i): self.I(0x09, t, s, i)
    def sltiu(self, t, s, i): self.I(0x0b, t, s, i)
    def slti(self, t, s, i): self.I(0x0a, t, s, i)
    def andi(self, t, s, i): self.I(0x0c, t, s, i)
    def ori(self, t, s, i): self.I(0x0d, t, s, i)
    def xori(self, t, s, i): self.I(0x0e, t, s, i)
    def lui(self, t, i): self.I(0x0f, t, 'zero', i)
    def lw(self, t, o, s): self.I(0x23, t, s, o); self.nop()
    def lh(self, t, o, s): self.I(0x21, t, s, o); self.nop()
    def lhu(self, t, o, s): self.I(0x25, t, s, o); self.nop()
    def lbu(self, t, o, s): self.I(0x24, t, s, o); self.nop()
    def sw(self, t, o, s): self.I(0x2b, t, s, o)
    def sh(self, t, o, s): self.I(0x29, t, s, o)
    def sb(self, t, o, s): self.I(0x28, t, s, o)
    def li(self, t, v):
        v &= 0xffffffff
        if v < 0x8000 or v >= 0xffff8000: self.addiu(t, 'zero', v & 0xffff)
        elif v & 0xffff == 0: self.lui(t, v >> 16)
        else:
            lo = v & 0xffff; hi = ((v >> 16) + (1 if lo & 0x8000 else 0)) & 0xffff
            self.lui(t, hi); self.addiu(t, t, lo)
    def la(self, t, name):   # address of label (resolved at build)
        self.items.append(lambda pc, L, t=t, n=name: (0x0f << 26) | (REG[t] << 16) | (((L[n] >> 16) + (1 if L[n] & 0x8000 else 0)) & 0xffff))
        self.items.append(lambda pc, L, t=t, n=name: (0x09 << 26) | (REG[t] << 21) | (REG[t] << 16) | (L[n] & 0xffff))
    def jal(self, a): self.raw((3 << 26) | ((a >> 2) & 0x3ffffff))
    def j(self, a): self.raw((2 << 26) | ((a >> 2) & 0x3ffffff))
    def jal_l(self, n): self.items.append(lambda pc, L, n=n: (3 << 26) | ((L[n] >> 2) & 0x3ffffff))
    def br(self, op, rs, rt, n):
        self.items.append(lambda pc, L, n=n: (op << 26) | (REG[rs] << 21) | (REG[rt] << 16) | (((L[n] - pc - 4) >> 2) & 0xffff))
    def beq(self, s, t, n): self.br(4, s, t, n)
    def bne(self, s, t, n): self.br(5, s, t, n)
    def b(self, n): self.br(4, 'zero', 'zero', n)
    def blez(self, s, n): self.br(6, s, 'zero', n)
    def build(self): return b''.join(struct.pack('<I', fn(self.org + 4 * i, self.labels)) for i, fn in enumerate(self.items))

# state block at EXT
S_ON, S_PREV, S_ALIVE, S_FRAME, S_TXT, S_OFFX, S_OFFY, S_LAY = 4, 16, 20, 24, 28, 32, 36, 40
S_SPK, S_KPREV, S_TIPTAB, S_WIDE = 44, 48, 52, 56

TIP_INLINE_TITLE = set(range(8)) | {12, 13, 14, 15}   # close-ups whose picture has a printed heading but no name card: flyers, notice, weekly motto, escapee reports
INST_TIP = ('{g}-\n{g}Sparkles\n'
            '{w}Press {g}SELECT{w} on a field screen to make the spots you can open sparkle. '
            'Press it again to turn them off.\n\n'
            'Sparkles only mark close-up views. Some other spots, like a bed or a muffler, '
            'just show a name label when you click them.')
SPKBTN = int(os.environ.get('SPKBTN', '0x100'), 0)   # Select (was L1 0x04)
SPKLAYER = int(os.environ.get('SPKLAYER', '2'))
SPKOPS = (23, 48)   # item-book (96) and shop LIST (81) hotspots already show an icon; op-96 rects are not the hotspot                              # close-up, shop LIST, item-book link
CARDY = int(os.environ.get('CARDY', '10'))     # vehicle card window y (orig 18)
TIPLAYER = int(os.environ.get('TIPLAYER', '0'))   # OT bucket for field close-up tooltips (in front of the popup)

def clutword(p): return ((CY << 6) | ((CX + 16 * p) >> 4)) & 0xffff

def build(exe, texts):
    assert FX % 64 == 0
    d = bytearray(exe)
    t_size = struct.unpack_from('<I', d, 0x1C)[0]; assert len(d) == 0x800 + t_size
    sheet, table = ovfont.build()
    sh_w, sh_h = sheet.size
    tpx, tpy = FX // 64, FY // 256; VOFF = FY - 256 * tpy
    assert VOFF + sh_h <= 256 and sh_w // 4 + FX <= 1024
    a = Asm(EXT + 64)
    ST = EXT
    # ================= stubA: item page input case (runs once per frame while an item page is up)
    a.L('stubA')
    a.li('t9', ST)
    # book = halfword BOOKSEL (0 weapons, 1 armor, 2 accessories, 3 items, 4 other); page index per book:
    #   0: EF38[gp+3012] + sum(EF60[< sub]);  3: EFB0[gp+3016] + sum(EFC4[< sub]);  else: EF88[book]
    a.li('t9', ST)
    a.li('t0', BOOKSEL); a.lh('t7', 0, 't0')
    a.bne('t7', 'zero', 'A_b3'); a.nop()
    a.lw('t0', CAT, 'gp'); a.li('t2', ITEMTAB); a.li('t3', COUNTS); a.b('A_sub'); a.nop()
    a.L('A_b3'); a.addiu('t1', 't7', -3); a.bne('t1', 'zero', 'A_b1'); a.nop()
    a.lw('t0', TOP, 'gp'); a.li('t2', 0x8009EFB0); a.li('t3', 0x8009EFC4); a.b('A_sub'); a.nop()
    a.L('A_b1'); a.sll('t1', 't7', 2); a.li('t2', 0x8009EF88); a.addu('t2', 't2', 't1'); a.lw('t1', 0, 't2'); a.b('A_look'); a.nop()
    a.L('A_sub')        # t0 = sub-list, t2 = item array, t3 = counts array
    a.sll('t1', 't0', 2); a.addu('t2', 't2', 't1'); a.lw('t1', 0, 't2'); a.move('t4', 'zero')
    a.L('A_sum'); a.beq('t4', 't0', 'A_look'); a.nop()
    a.lw('t5', 0, 't3'); a.addiu('t3', 't3', 4); a.addu('t1', 't1', 't5'); a.b('A_sum'); a.addiu('t4', 't4', 1)
    def tail(P):
        a.L(P+'look')
        a.move('t5', 'zero'); a.sltiu('t8', 't7', 8); a.beq('t8', 'zero', P+'tz'); a.nop()
        a.la('t3', 'BOOKS'); a.sll('t4', 't7', 3); a.addu('t3', 't3', 't4')
        a.lw('t5', 0, 't3'); a.lw('t6', 4, 't3')
        a.L(P+'tz')
        a.move('t7', 'zero'); a.sltu('t8', 't1', 't5'); a.beq('t8', 'zero', P+'txt'); a.nop()
        a.sll('t8', 't1', 2); a.addu('t6', 't6', 't8'); a.lw('t7', 0, 't6')
        a.L(P+'txt'); a.sw('t7', S_TXT, 't9')
        a.lw('t0', S_FRAME, 't9'); a.sw('t0', S_ALIVE, 't9')
        a.li('t8', RAWPAD); a.lhu('t0', 0, 't8')
        a.lw('t1', S_PREV, 't9'); a.sw('t0', S_PREV, 't9'); a.nor('t1', 'zero', 't1'); a.and_('t0', 't0', 't1')
        a.andi('t1', 't0', 0x40); a.beq('t1', 'zero', P+'tri'); a.nop()
        a.lw('t1', S_FRAME, 't9'); a.addiu('t1', 't1', -100); a.sw('t1', S_ALIVE, 't9')   # CROSS: book is closing, stop drawing now
        a.L(P+'tri')
        a.andi('t1', 't0', 0x10); a.beq('t1', 'zero', P+'done'); a.nop()
        a.lw('t1', S_ON, 't9'); a.xori('t1', 't1', 1); a.sw('t1', S_ON, 't9')
        a.L(P+'done')
    tail('A_')
    a.lui('v1', 0x800c); a.lh('v1', -17364, 'v1'); a.j(BACK_IN); a.nop()

    # ================= stubF: field-launched item page (screen 0x8009F3CC, update 0x80026AD4)
    #   book = gp+4284, page = gp+4224 (same numbering as the item viewer's global page index)
    a.L('stubF')
    a.li('t9', ST)
    a.lw('t7', 4284, 'gp'); a.lw('t1', 4224, 'gp')
    tail('F_')
    a.lui('v0', 0x800c); a.lhu('v0', -17340, 'v0'); a.j(FBACK); a.nop()

    # ================= stubS: shop LIST page (screen 0x8009F608, update 0x80028080); gp+3660 == 1 while the page is shown
    #   (0 = the shop list is open over the book: draw nothing). The shop sets gp+4224/4284 like the field page.
    def shop_stub(name, P, back):
        a.L(name)
        a.lw('t0', 3660, 'gp'); a.addiu('t0', 't0', -1); a.bne('t0', 'zero', P+'out'); a.nop()
        a.li('t9', ST)
        a.lw('t7', 4284, 'gp'); a.lw('t1', 4224, 'gp')
        tail(P)
        a.L(P+'out')
        a.lui('v0', 0x800c); a.lhu('v0', -17340, 'v0'); a.j(back); a.nop()
    shop_stub('stubS', 'S_', SBACK)     # shop screen 0x8009F608 (update 0x80028080)
    shop_stub('stubS2', 'T_', SBACK2)   # shop screen 0x8009F554 (update 0x80027A94) - e.g. Cosmo/Nibelheim item shops

    # ================= stubY: vehicle data card - centre the window vertically instead of y=18
    #   hook replaces 'addiu a2,zero,18' at 0x80030DDC (s2 = window height); its delay slot is the original next insn
    a.L('stubY')
    a.addiu('a2', 'zero', 240); a.subu('a2', 'a2', 's2'); a.sra('a2', 'a2', 1)
    a.slti('t0', 'a2', 4); a.beq('t0', 'zero', 'Y_ok'); a.nop(); a.addiu('a2', 'zero', 4)
    a.L('Y_ok')
    a.jr('ra'); a.nop()

    # ================= stubK: hotspot sparkles on field screens (toggle with L1; off at power-on)
    a.L('stubK')
    a.addiu('sp', 'sp', -40); a.sw('ra', 32, 'sp'); a.sw('s0', 28, 'sp'); a.sw('s1', 24, 'sp'); a.sw('s2', 20, 'sp'); a.sw('s3', 16, 'sp'); a.sw('s7', 12, 'sp')
    a.lw('t0', 4036, 'gp'); a.li('t1', 0x8009D1C4); a.bne('t0', 't1', 'K_out'); a.nop()
    a.li('t9', ST)
    a.li('t0', RAWPAD); a.lhu('t0', 0, 't0'); a.andi('t0', 't0', SPKBTN)
    a.lw('t1', S_KPREV, 't9'); a.sw('t0', S_KPREV, 't9')
    a.beq('t0', 'zero', 'K_nt'); a.nop(); a.bne('t1', 'zero', 'K_nt'); a.nop()
    a.lw('t2', S_SPK, 't9'); a.xori('t2', 't2', 1); a.sw('t2', S_SPK, 't9')
    a.L('K_nt')
    a.lw('t2', S_SPK, 't9'); a.beq('t2', 'zero', 'K_out'); a.nop()
    # OT bucket SPKLAYER of this frame -> s7 ; prim pointer -> s3
    a.li('t0', ADDR_FRAME); a.lw('t0', 0, 't0'); a.sll('t1', 't0', 2); a.addu('t1', 't1', 't0'); a.sll('t1', 't1', 2)
    a.li('t2', OTDESC); a.addu('t1', 't1', 't2')
    a.lw('t2', 4, 't1'); a.lw('t3', 8, 't1'); a.addiu('t4', 'zero', SPKLAYER); a.subu('t4', 't4', 't3'); a.sll('t4', 't4', 2)
    a.addu('s7', 't2', 't4')
    a.li('t0', PRIMPTR); a.lw('s3', 0, 't0')
    a.li('s0', 0x801EF3C8); a.li('t0', 0x801EF364); a.lb('s1', 0, 't0'); a.move('s2', 'zero')
    a.L('K_loop')
    a.slt('t0', 's2', 's1'); a.beq('t0', 'zero', 'K_done'); a.nop()
    a.lh('t0', 0, 's0')
    a.addiu('t1', 'zero', 23); a.beq('t0', 't1', 'K_draw'); a.nop()
    a.addiu('t1', 'zero', 48); a.beq('t0', 't1', 'K_draw'); a.nop()
    a.b('K_next'); a.nop()
    a.L('K_draw')
    # phase = (frame + 11*i) & 31 ; visible for phase < 16, arm 1..4 rising then falling
    a.li('t9', ST); a.lw('t0', S_FRAME, 't9'); a.sll('t1', 's2', 3); a.addu('t0', 't0', 't1'); a.sll('t1', 's2', 1); a.addu('t0', 't0', 't1'); a.addu('t0', 't0', 's2')
    a.andi('t0', 't0', 127); a.sltiu('t1', 't0', 16); a.beq('t1', 'zero', 'K_next'); a.nop()
    a.sltiu('t1', 't0', 8); a.bne('t1', 'zero', 'K_up'); a.nop()
    a.addiu('t2', 'zero', 15); a.subu('t0', 't2', 't0')
    a.L('K_up')
    a.srl('t0', 't0', 1); a.addiu('t0', 't0', 1); a.sw('t0', 36, 'sp')            # arm length L
    # centre in screen coords + draw offset (screen offset - 256/120)
    # a hotspot's rectangle (x0,y0,x1,y1) is the 8 bytes *before* its op/arg/label (i.e. +8 of the previous slot)
    a.lh('t1', -8, 's0'); a.lh('t2', -4, 's0'); a.addu('t1', 't1', 't2'); a.sra('t1', 't1', 1)
    a.lh('t2', -6, 's0'); a.lh('t3', -2, 's0'); a.addu('t2', 't2', 't3'); a.sra('t2', 't2', 1)
    a.li('t3', SCROFF); a.lh('t4', 0, 't3'); a.addiu('t4', 't4', -256); a.addu('t1', 't1', 't4')
    a.lh('t4', 2, 't3'); a.addiu('t4', 't4', -120); a.addu('t2', 't2', 't4')
    a.sw('t1', 4, 'sp'); a.sw('t2', 8, 'sp')
    # horizontal arm
    a.lw('t0', 36, 'sp'); a.srl('t3', 't0', 1); a.addu('t0', 't0', 't3'); a.subu('a0', 't1', 't0'); a.move('a1', 't2'); a.sll('a2', 't0', 1); a.addiu('a2', 'a2', 2); a.addiu('a3', 'zero', 1)
    a.li('t0', 0x60C0F0F8); a.jal_l('tile'); a.nop()
    # vertical arm
    a.lw('t0', 36, 'sp'); a.lw('a0', 4, 'sp'); a.lw('a1', 8, 'sp'); a.subu('a1', 'a1', 't0'); a.addiu('a2', 'zero', 2); a.sll('a3', 't0', 1); a.addiu('a3', 'a3', 1)
    a.li('t0', 0x60C0F0F8); a.jal_l('tile'); a.nop()
    # bright core
    a.lw('a0', 4, 'sp'); a.lw('a1', 8, 'sp'); a.addiu('a2', 'zero', 2); a.addiu('a3', 'zero', 1)
    a.li('t0', 0x60FFFFFF); a.jal_l('tile'); a.nop()
    a.lw('t0', 36, 'sp'); a.sltiu('t0', 't0', 4); a.bne('t0', 'zero', 'K_next'); a.nop()
    for dx, dy in ((-3, -2), (4, -2), (-3, 2), (4, 2)):
        a.lw('a0', 4, 'sp'); a.addiu('a0', 'a0', dx); a.lw('a1', 8, 'sp'); a.addiu('a1', 'a1', dy); a.addiu('a2', 'zero', 2); a.addiu('a3', 'zero', 1)
        a.li('t0', 0x6080C0D0); a.jal_l('tile'); a.nop()
    a.L('K_next')
    a.addiu('s0', 's0', 16); a.b('K_loop'); a.addiu('s2', 's2', 1)
    a.L('K_done')
    a.li('t0', PRIMPTR); a.sw('s3', 0, 't0')
    a.L('K_out')
    a.lw('ra', 32, 'sp'); a.lw('s0', 28, 'sp'); a.lw('s1', 24, 'sp'); a.lw('s2', 20, 'sp'); a.lw('s3', 16, 'sp'); a.lw('s7', 12, 'sp')
    a.jr('ra'); a.addiu('sp', 'sp', 40)

    # ================= stubR: Krom2RawAdd hook - our own 16x15 bitmaps for the Roman numerals in "Red XIII"
    # (BIOS kanji glyphs are bold and taller than the 8x16 English font; these match its cap rows 2..14, 1px strokes)
    a.L('stubR')
    a.li('at', 0x875D); a.beq('a0', 'at', 'KR_X'); a.nop()
    a.li('at', 0x8756); a.beq('a0', 'at', 'KR_3'); a.nop()
    a.li('t2', 0xB0); a.jr('t2'); a.li('t1', 0x51)
    a.L('KR_X'); a.la('v0', 'GLYPH_X'); a.jr('ra'); a.nop()
    a.L('KR_3'); a.la('v0', 'GLYPH_3'); a.jr('ra'); a.nop()

    # ================= stubP: field close-up tooltips. Called from stubC every frame.
    #   field screen (gp+4036 == 0x8009D1C4), hovered record gp+2992 is a close-up hotspot (op 48) whose picture is up
    #   (halfword 0x800BBB32 == arg+1); its label pointer is looked up in TIPKEYS -> text set 5.
    a.L('stubP')
    a.li('t9', ST); a.addiu('t0', 'zero', LAYER); a.sw('t0', S_LAY, 't9'); a.sw('zero', S_TIPTAB, 't9'); a.sw('zero', S_WIDE, 't9')
    # instructions screen (0x8009C530), controller page (halfword 0x800BBB32 == 0): "Tip" about sparkles, last entry of set 5
    a.lw('t0', 4036, 'gp'); a.li('t1', 0x8009C530); a.bne('t0', 't1', 'P_fld'); a.nop()
    a.li('t4', 0x800BBB32); a.lh('t4', 0, 't4'); a.bne('t4', 'zero', 'P_out'); a.nop()
    a.addiu('t7', 'zero', 5); a.la('t1', 'INSTTIP'); a.lw('t1', 0, 't1')
    a.addiu('t0', 'zero', 1); a.sw('t0', S_TIPTAB, 't9'); a.sw('t0', S_WIDE, 't9')
    a.addiu('t0', 'zero', TIPLAYER); a.sw('t0', S_LAY, 't9')
    tail('I_')
    a.jr('ra'); a.nop()
    a.L('P_fld')
    a.lw('t0', 4036, 'gp'); a.li('t1', 0x8009D1C4); a.bne('t0', 't1', 'P_out'); a.nop()
    a.lw('t0', 2992, 'gp'); a.sll('t0', 't0', 4); a.li('t1', 0x801EF3C8); a.addu('t1', 't1', 't0')
    a.lh('t2', 0, 't1'); a.addiu('t2', 't2', -48); a.bne('t2', 'zero', 'P_out'); a.nop()
    a.lh('t5', 2, 't1'); a.addiu('t3', 't5', 1); a.li('t4', 0x800BBB32); a.lh('t4', 0, 't4')
    a.bne('t3', 't4', 'P_out'); a.nop()
    a.lw('t2', 4, 't1'); a.la('t3', 'TIPKEYS'); a.move('t1', 'zero')
    a.L('P_find'); a.lw('t4', 0, 't3'); a.beq('t4', 'zero', 'P_out'); a.nop()
    a.bne('t4', 't2', 'P_next'); a.nop()
    a.lw('t4', 4, 't3'); a.beq('t4', 't5', 'P_hit'); a.nop()
    a.L('P_next')
    a.addiu('t3', 't3', 8); a.b('P_find'); a.addiu('t1', 't1', 1)
    a.L('P_hit')
    a.li('t9', ST); a.addiu('t7', 'zero', 5)
    a.addiu('t0', 'zero', 1); a.sw('t0', S_WIDE, 't9')
    a.addiu('t0', 'zero', TIPLAYER); a.sw('t0', S_LAY, 't9')
    tail('P_')
    a.L('P_out')
    a.jr('ra'); a.nop()

    # ================= addprim macro: prim in reg p, n words; ote in s7
    def addprim(p, n):
        a.lw('t8', 0, 's7'); a.sw('t8', 0, p); a.addiu('t8', 'zero', n); a.sb('t8', 3, p)
        a.sw(p, 0, 's7'); a.sb('zero', 3, 's7')

    # ================= tile(a0 x, a1 y, a2 w, a3 h, t0 colorword) -> uses s3 prim ptr
    a.L('tile')
    a.sw('t0', 4, 's3')
    a.sll('t1', 'a1', 16); a.andi('t2', 'a0', 0xffff); a.or_('t1', 't1', 't2'); a.sw('t1', 8, 's3')
    a.sll('t1', 'a3', 16); a.or_('t1', 't1', 'a2'); a.sw('t1', 12, 's3')
    addprim('s3', 3); a.jr('ra'); a.addiu('s3', 's3', 16)

    # ================= box(a0 x, a1 y, a2 w, a3 h): border tiles then gradient (gradient added last => drawn first)
    a.L('box')
    a.addiu('sp', 'sp', -40); a.sw('ra', 32, 'sp'); a.sw('a0', 16, 'sp'); a.sw('a1', 20, 'sp'); a.sw('a2', 24, 'sp'); a.sw('a3', 28, 'sp')
    def reload():
        a.lw('a0', 16, 'sp'); a.lw('a1', 20, 'sp'); a.lw('a2', 24, 'sp'); a.lw('a3', 28, 'sp')
    OUT, INN = 0x60282828, 0x60D0D0D0
    # inner light frame (1px, inset 1)
    def edge(col, inset):
        # top
        reload(); a.addiu('a0', 'a0', inset); a.addiu('a1', 'a1', inset); a.addiu('a2', 'a2', -2 * inset); a.addiu('a3', 'zero', 1)
        a.li('t0', col); a.jal_l('tile'); a.nop()
        # bottom
        reload(); a.addiu('a0', 'a0', inset); a.addu('a1', 'a1', 'a3'); a.addiu('a1', 'a1', -1 - inset); a.addiu('a2', 'a2', -2 * inset); a.addiu('a3', 'zero', 1)
        a.li('t0', col); a.jal_l('tile'); a.nop()
        # left
        reload(); a.addiu('a0', 'a0', inset); a.addiu('a1', 'a1', inset); a.addiu('a2', 'zero', 1); a.addiu('a3', 'a3', -2 * inset)
        a.li('t0', col); a.jal_l('tile'); a.nop()
        # right
        reload(); a.addu('a0', 'a0', 'a2'); a.addiu('a0', 'a0', -1 - inset); a.addiu('a1', 'a1', inset); a.addiu('a2', 'zero', 1); a.addiu('a3', 'a3', -2 * inset)
        a.li('t0', col); a.jal_l('tile'); a.nop()
    edge(INN, 1); edge(OUT, 0)
    # gradient POLY_G4: 0x38
    reload()
    a.addu('t2', 'a0', 'a2'); a.addu('t3', 'a1', 'a3')        # x1, y1
    a.sll('t4', 'a1', 16); a.sll('t5', 't3', 16)
    a.li('t0', 0x38B01000); a.sw('t0', 4, 's3')
    a.andi('a0', 'a0', 0xffff); a.andi('t2', 't2', 0xffff)
    a.or_('t1', 't4', 'a0'); a.sw('t1', 8, 's3')
    a.li('t0', 0x00800800); a.sw('t0', 12, 's3')
    a.or_('t1', 't4', 't2'); a.sw('t1', 16, 's3')
    a.li('t0', 0x00580400); a.sw('t0', 20, 's3')
    a.or_('t1', 't5', 'a0'); a.sw('t1', 24, 's3')
    a.li('t0', 0x00300000); a.sw('t0', 28, 's3')
    a.or_('t1', 't5', 't2'); a.sw('t1', 32, 's3')
    addprim('s3', 8); a.addiu('s3', 's3', 36)
    a.lw('ra', 32, 'sp'); a.jr('ra'); a.addiu('sp', 'sp', 40)

    # ================= text(a0 ptr, a1 x, a2 y): glyph SPRTs
    a.L('text')
    a.addiu('sp', 'sp', -40); a.sw('ra', 32, 'sp'); a.sw('s0', 28, 'sp'); a.sw('s1', 24, 'sp'); a.sw('s2', 20, 'sp'); a.sw('s4', 16, 'sp')
    a.sw('s5', 36, 'sp'); a.sw('s6', 8, 'sp')
    a.move('s0', 'a0'); a.move('s1', 'a1'); a.move('s5', 'a1'); a.move('s2', 'a2'); a.li('s4', clutword(0) << 16)
    a.move('s6', 'zero')                                   # return pointer while expanding a dictionary token
    a.L('T_loop')
    a.lbu('t0', 0, 's0'); a.addiu('s0', 's0', 1)
    a.bne('t0', 'zero', 'T_nz'); a.nop()
    a.beq('s6', 'zero', 'T_end'); a.nop()
    a.move('s0', 's6'); a.b('T_loop'); a.move('s6', 'zero')
    a.L('T_nz')
    a.sltiu('t1', 't0', TOK0); a.bne('t1', 'zero', 'T_plain'); a.nop()
    a.bne('s6', 'zero', 'T_plain'); a.nop()                 # (tokens never nest)
    a.move('s6', 's0'); a.la('t1', 'TOKOFS'); a.addiu('t2', 't0', -TOK0); a.sll('t2', 't2', 1); a.addu('t1', 't1', 't2')
    a.lhu('t2', 0, 't1'); a.la('s0', 'TOKBLOB'); a.b('T_loop'); a.addu('s0', 's0', 't2')
    a.L('T_plain')
    a.addiu('t1', 't0', -10); a.bne('t1', 'zero', 'T_n1'); a.nop()
    a.move('s1', 's5'); a.b('T_loop'); a.addiu('s2', 's2', LH)
    a.L('T_n1'); a.addiu('t1', 't0', -9); a.bne('t1', 'zero', 'T_n2'); a.nop()
    a.b('T_loop'); a.addiu('s1', 's5', TABX)
    a.L('T_n2'); a.addiu('t1', 't0', -4); a.bne('t1', 'zero', 'T_n3'); a.nop()
    a.b('T_loop'); a.addiu('s1', 's5', ovtext.INDENT)                     # 4 = hanging indent
    a.L('T_n3'); a.sltiu('t1', 't0', 4); a.beq('t1', 'zero', 'T_glyph'); a.nop()
    # 1 gold, 2 white, 3 cyan
    a.li('s4', clutword(1) << 16); a.addiu('t1', 't0', -1); a.beq('t1', 'zero', 'T_loop'); a.nop()
    a.li('s4', clutword(0) << 16); a.addiu('t1', 't0', -2); a.beq('t1', 'zero', 'T_loop'); a.nop()
    a.b('T_loop'); a.lui('s4', clutword(2))
    a.L('T_glyph')
    a.la('t1', 'GTAB'); a.sll('t2', 't0', 3); a.addu('t1', 't1', 't2')
    a.lbu('t2', 0, 't1'); a.lbu('t3', 1, 't1'); a.lbu('t4', 2, 't1'); a.lbu('t5', 3, 't1')     # u v w adv
    a.beq('t4', 'zero', 'T_adv'); a.nop()
    a.li('t6', 0x65808080); a.sw('t6', 4, 's3')
    a.sll('t6', 's2', 16); a.andi('t7', 's1', 0xffff); a.or_('t6', 't6', 't7'); a.sw('t6', 8, 's3')
    if VOFF: a.addiu('t3', 't3', VOFF)
    a.sll('t3', 't3', 8)
    a.lbu('t7', 5, 't1'); a.beq('t7', 'zero', 'T_pal'); a.or_('t6', 's4', 't3')       # glyph with its own CLUT (icon)
    a.addiu('t7', 't7', clutword(0) - 1); a.sll('t7', 't7', 16); a.or_('t6', 't7', 't3')
    a.L('T_pal'); a.or_('t6', 't6', 't2'); a.sw('t6', 12, 's3')
    a.lui('t6', GH); a.or_('t6', 't6', 't4'); a.sw('t6', 16, 's3')
    addprim('s3', 4); a.addiu('s3', 's3', 20)
    # its texture page (added after the sprite => executed right before it)
    a.lbu('t2', 4, 't1'); a.li('t6', 0xE1000200 | tpx | (tpy << 4)); a.addu('t6', 't6', 't2'); a.sw('t6', 4, 's3')
    addprim('s3', 1); a.addiu('s3', 's3', 8)
    a.L('T_adv'); a.b('T_loop'); a.addu('s1', 's1', 't5')
    a.L('T_end')
    a.lw('ra', 32, 'sp'); a.lw('s0', 28, 'sp'); a.lw('s1', 24, 'sp'); a.lw('s2', 20, 'sp'); a.lw('s4', 16, 'sp'); a.lw('s5', 36, 'sp')
    a.lw('s6', 8, 'sp')
    a.jr('ra'); a.addiu('sp', 'sp', 40)

    # ================= stubC: scheduler hook (replaces 'jal SCHED_FN', delay slot a0=1 kept)
    a.L('stubC')
    a.addiu('sp', 'sp', -48); a.sw('ra', 40, 'sp'); a.sw('a0', 36, 'sp'); a.sw('s3', 32, 'sp'); a.sw('s6', 28, 'sp'); a.sw('s7', 24, 'sp')
    a.li('s6', ST)
    a.lw('t0', S_FRAME, 's6'); a.addiu('t0', 't0', 1); a.sw('t0', S_FRAME, 's6')
    a.jal_l('stubP'); a.nop()
    a.jal_l('stubK'); a.nop()
    a.lw('t0', S_FRAME, 's6')
    a.lw('t1', S_ALIVE, 's6'); a.subu('t1', 't0', 't1'); a.sltiu('t1', 't1', 2); a.beq('t1', 'zero', 'C_end'); a.nop()
    a.lw('t1', S_TXT, 's6'); a.beq('t1', 'zero', 'C_end'); a.nop()          # no English for this page (e.g. Materia): draw nothing
    # OT entry for LAYER of this frame
    a.li('t0', ADDR_FRAME); a.lw('t0', 0, 't0'); a.sll('t1', 't0', 2); a.addu('t1', 't1', 't0'); a.sll('t1', 't1', 2)
    a.li('t2', OTDESC); a.addu('t1', 't1', 't2')
    a.lw('t2', 4, 't1'); a.lw('t3', 8, 't1'); a.lw('t4', S_LAY, 's6'); a.subu('t4', 't4', 't3'); a.sll('t4', 't4', 2)
    a.addu('s7', 't2', 't4')
    a.li('t0', SCROFF); a.lh('t1', 0, 't0'); a.addiu('t1', 't1', -256); a.sw('t1', S_OFFX, 's6')
    a.lh('t1', 2, 't0'); a.addiu('t1', 't1', -120); a.sw('t1', S_OFFY, 's6')   # page screen draws with origin at screen centre
    # upload font + cluts (re-sent every frame: page loads reuse VRAM)
    a.la('a0', 'RFONT'); a.la('a1', 'FONT'); a.jal(LOADIMAGE); a.nop()
    a.la('a0', 'RCLUT'); a.la('a1', 'CLUT'); a.jal(LOADIMAGE); a.nop()
    a.li('t0', PRIMPTR); a.lw('s3', 0, 't0')
    # main text (if on and present)
    a.lw('t0', S_ON, 's6'); a.beq('t0', 'zero', 'C_tab'); a.nop()
    a.lw('a0', S_TXT, 's6'); a.beq('a0', 'zero', 'C_tab'); a.nop()
    a.lbu('t1', 2, 'a0'); a.addiu('a0', 'a0', 4); a.addu('a0', 'a0', 't1')      # body follows [bh][nh][namelen][bw][name]
    a.lw('t2', S_WIDE, 's6'); a.sll('t2', 't2', 4); a.la('t3', 'GEOM'); a.addu('t3', 't3', 't2')   # t3 -> [x, y, w]
    a.lw('a1', S_OFFX, 's6'); a.lw('t4', 0, 't3'); a.addu('a1', 'a1', 't4'); a.addiu('a1', 'a1', PADX)
    a.lw('a2', S_OFFY, 's6'); a.lw('t4', 4, 't3'); a.addu('a2', 'a2', 't4'); a.addiu('a2', 'a2', PADY - INK_TOP)
    a.jal_l('text'); a.nop()
    # item name over the Japanese title
    a.lw('a0', S_TXT, 's6'); a.lbu('t1', 2, 'a0'); a.beq('t1', 'zero', 'C_tab'); a.nop()   # no name box
    a.addiu('a0', 'a0', 4)
    a.lw('a1', S_OFFX, 's6'); a.addiu('a1', 'a1', NX + PADX)
    a.lw('a2', S_OFFY, 's6'); a.addiu('a2', 'a2', NY + (NH - (BASE_BOT - INK_TOP + 1)) // 2 - INK_TOP)
    a.jal_l('text'); a.nop()
    a.L('C_tab')
    # tab text
    a.lw('t0', S_ON, 's6'); a.la('a0', 'TABON'); a.bne('t0', 'zero', 'C_tab2'); a.nop()
    a.lw('t0', S_TIPTAB, 's6'); a.la('a0', 'TABOFF'); a.beq('t0', 'zero', 'C_tab2'); a.nop(); a.la('a0', 'TABTIP')
    a.L('C_tab2')
    a.lbu('t1', 0, 'a0'); a.addiu('a0', 'a0', 1)
    a.lw('a1', S_OFFX, 's6'); a.addu('a1', 'a1', 't1'); a.addiu('a1', 'a1', 256)
    a.lw('a2', S_OFFY, 's6'); a.addiu('a2', 'a2', TABY + 4 - INK_TOP)
    a.jal_l('text'); a.nop()
    # boxes
    a.lw('t0', S_ON, 's6'); a.beq('t0', 'zero', 'C_box2'); a.nop()
    a.lw('t0', S_TXT, 's6'); a.beq('t0', 'zero', 'C_box2'); a.nop()
    a.lbu('a3', 0, 't0')
    a.lw('t2', S_WIDE, 's6'); a.sll('t2', 't2', 4); a.la('t3', 'GEOM'); a.addu('t3', 't3', 't2')
    a.lw('a0', S_OFFX, 's6'); a.lw('t4', 0, 't3'); a.addu('a0', 'a0', 't4')
    a.lw('a1', S_OFFY, 's6'); a.lw('t4', 4, 't3'); a.addu('a1', 'a1', 't4')
    a.lw('t0', S_TXT, 's6'); a.lbu('a2', 3, 't0'); a.sll('a2', 'a2', 1)          # per-text box width
    a.jal_l('box'); a.nop()
    a.lw('a0', S_OFFX, 's6'); a.addiu('a0', 'a0', NX); a.lw('a1', S_OFFY, 's6'); a.addiu('a1', 'a1', NY)
    a.lw('t0', S_TXT, 's6'); a.lbu('t1', 2, 't0'); a.beq('t1', 'zero', 'C_box2'); a.nop()
    a.addiu('a2', 'zero', NW); a.lbu('a3', 1, 't0')
    a.jal_l('box'); a.nop()
    a.L('C_box2')
    a.la('t0', 'TABBOX'); a.lhu('a0', 0, 't0'); a.lhu('a2', 2, 't0')
    a.lw('t1', S_OFFX, 's6'); a.addu('a0', 'a0', 't1')
    a.lw('a1', S_OFFY, 's6'); a.addiu('a1', 'a1', TABY); a.addiu('a3', 'zero', TABH)
    a.jal_l('box'); a.nop()
    a.li('t0', PRIMPTR); a.sw('s3', 0, 't0')
    a.L('C_end')
    a.lw('ra', 40, 'sp'); a.lw('a0', 36, 'sp'); a.lw('s3', 32, 'sp'); a.lw('s6', 28, 'sp'); a.lw('s7', 24, 'sp')
    a.addiu('sp', 'sp', 48)
    a.j(SCHED_FN); a.nop()

    # ================= startup BSS clear that skips our segment
    a.L('clr')
    a.li('v0', BSS_LO); a.li('v1', EXT)
    a.L('CL1'); a.sw('zero', 0, 'v0'); a.addiu('v0', 'v0', 4); a.sltu('at', 'v0', 'v1'); a.bne('at', 'zero', 'CL1'); a.nop()
    a.la('v0', 'SEGEND'); a.li('v1', BSS_HI)
    a.L('CL2'); a.sw('zero', 0, 'v0'); a.addiu('v0', 'v0', 4); a.sltu('at', 'v0', 'v1'); a.bne('at', 'zero', 'CL2'); a.nop()
    a.j(START_BACK); a.nop()

    # ================= data
    data = []      # (label, bytes) placed after code, 4-aligned
    def put(lbl, b): data.append((lbl, bytes(b) + b'\0' * ((-len(b)) % 4)))
    put('RFONT', struct.pack('<hhhh', FX, FY, sh_w // 4, sh_h))
    put('RCLUT', struct.pack('<hhhh', CX, CY, 64, 1))
    put('TABBOX', b'')   # filled below
    cl = ovfont.clut_words(); put('CLUT', b''.join(struct.pack('<16H', *r) for r in cl))
    gt = bytearray(2048)
    for code, (u, v, w, adv, strip, pal) in table.items():
        gt[code * 8: code * 8 + 6] = bytes([u, v, w, min(adv, 255), strip, pal])
    put('GTAB', gt)
    put('FONT', ovfont.pack4(sheet))
    NSF = os.environ.get('NAMESORT', '/home/claude/mlist/namesort.bin')
    put('NAMESORT', open(NSF, 'rb').read())
    put('GEOM', struct.pack('<8I', WX, WY, WW, 0, WX2, WY2, WW2, 0))
    put('MASAMUNE', b'Masamune\0')      # Sephiroth's weapon; original slot is 7 bytes
    put('SELEM', b'\nElem.  \0')     # summon page: widened label (original slot can't grow)
    def kglyph(rows):
        out = b''
        for r in range(15):
            v = int(rows[r].replace('#', '1').replace('.', '0'), 2) if r < len(rows) else 0
            out += struct.pack('>H', v)
        return out
    put('GLYPH_X', kglyph(['................', '................',
        '.#############..', '..#.......#.....', '..#.......#.....', '...#.....#......', '....#...#.......',
        '.....#.#........', '......#.........', '.....#.#........', '....#...#.......', '...#.....#......',
        '..#.......#.....', '..#.......#.....', '.#############..']))
    put('GLYPH_3', kglyph(['................', '................',
        '.###########....', '..#...#...#.....', '..#...#...#.....', '..#...#...#.....', '..#...#...#.....',
        '..#...#...#.....', '..#...#...#.....', '..#...#...#.....', '..#...#...#.....', '..#...#...#.....',
        '..#...#...#.....', '..#...#...#.....', '.###########....']))
    # instructions-screen tip: appended to text set 5 (after the field tooltips, which are matched via TIPKEYS)
    texts = dict(texts); texts['5'] = list(texts['5']) + [INST_TIP]
    put('INSTTIP', struct.pack('<I', len(texts['5']) - 1))
    # tab strings: first byte = x offset of text
    ton, toff, ttip = '{g}△{w} Hide', '{g}△{w} English', '{g}△{w} Tip'
    bon, boff, btip = ovtext.encode(ton), ovtext.encode(toff), ovtext.encode(ttip)
    wmax = max(ovtext.layout(b, table, 0, 0, TABX, LH)[1] for b in (bon, boff, btip))
    tabw = wmax + 10; tabx = WX + WW - tabw
    data = [(l, b) if l != 'TABBOX' else (l, struct.pack('<HH', tabx, tabw)) for l, b in data]
    # texts
    texts = dict(texts); tipkeys = texts.pop('tipkeys', [])
    cats = {int(k): v for k, v in texts.items()}
    tipptrs = []
    for r in tipkeys:
        ra = int(r, 16); ro = ra - 0x80010200 + 0x800
        op = struct.unpack_from('<h', d, ro)[0]; assert op == 48, (r, op)
        tipptrs += [struct.unpack_from('<I', d, ro + 4)[0], struct.unpack_from('<h', d, ro + 2)[0]]   # (label ptr, arg)
    put('TIPKEYS', struct.pack('<%dI' % (len(tipptrs) + 2), *tipptrs, 0, 0))
    strs = []
    report = []
    for c in sorted(cats):
        lst = cats[c]
        for i, s in enumerate(lst):
            if not s: strs.append((c, i, None)); continue
            name, s = s.split('\n', 1)
            if c == 5:                 # close-up tips have no title box (the Japanese close-ups show none)...
                if i in TIP_INLINE_TITLE and name.replace('{g}', '').strip():
                    s = '{g}' + name.replace('{g}', '') + '\n' + s   # ...but flyers carry a printed heading: show it as the first line
                name = ''
            name = name.replace('\\n', '\n').replace('{g}', '')
            if name: name = ovtext.wrap('{g}' + name, table, NW - 2 * PADX, TABX)[3:]
            nameb = ovtext.encode('{g}' + name) if name else b''
            if name: assert ovtext.layout(nameb, table, 0, 0, TABX, LH)[1] <= NW - 2 * PADX, ('name too wide', name)
            nh = NH + LH * name.count('\n')
            if not name: nameb = b''
            ww, wy = (WW2, WY2) if c == 5 else (WW, WY)
            s = ovtext.wrap(s, table, ww - 2 * PADX, TABX)
            b = ovtext.encode(s)
            glyphs, tw, th = ovtext.layout(b, table, 0, 0, TABX, LH)
            nl = b.count(10) + 1
            last = s.split('\n')[-1]
            bot = BASE_BOT          # pad from the baseline; descenders may hang into the bottom padding
            bh = (nl - 1) * LH + (bot - INK_TOP + 1) + 2 * PADY
            if tw > ww - 2 * PADX or wy + bh > MAXBOT:
                report.append((c, i, nl, tw, bh, s.split('\n')[0]))
                if not os.environ.get('OVLAX'): continue
            bw = WW // 2 if c != 5 else (min(WW2, tw + 2 * PADX + 2) + 1) // 2   # box width / 2: wide tips hug their longest line
            strs.append((c, i, bytes([bh, nh, len(nameb), bw]) + nameb + b))
    if report:
        print('DOES NOT FIT:'); [print('  ', r) for r in report]
        if not os.environ.get('OVLAX'): raise SystemExit(1)
    # layout data after code
    code_len = len(a.items) * 4
    pos = EXT + 64 + code_len
    labels = {}
    blob = bytearray()
    for lbl, b in data:
        labels[lbl] = pos + len(blob); blob += b
    # tab strings with absolute x as first byte relative to 256
    for lbl, b in (('TABON', bon), ('TABOFF', boff), ('TABTIP', btip)):
        w = ovtext.layout(b, table, 0, 0, TABX, LH)[1]
        x = tabx + 5                        # left-aligned: icon stays put when the label changes
        assert 256 <= x < 512
        labels[lbl] = pos + len(blob); blob += bytes([x - 256]) + b; blob += b'\0' * ((-len(blob)) % 4)
    # CATTAB + arrays + strings
    labels['BOOKS'] = pos + len(blob); bk_off = len(blob); blob += b'\0' * 64
    arr = {}
    for c in sorted(cats):
        n = len(cats[c]); slot = BOOKIDX[c]
        arr[c] = pos + len(blob); struct.pack_into('<II', blob, bk_off + 8 * slot, n, arr[c]); blob += b'\0' * (4 * n)
    # --- dictionary compression of all bodies/names
    import tokcomp
    keys = [(c, i) for c, i, b in strs if b is not None]
    raws = [b for c, i, b in strs if b is not None]
    heads = [r[:4] for r in raws]
    name_body = [r[4:] for r in raws]
    toks, comp = tokcomp.build(name_body, 0x100 - TOK0)
    # name length byte must reflect the compressed name (name ends at its own terminator)
    newraw = []
    for h, cb in zip(heads, comp):
        nlen = cb.index(0) + 1 if h[2] else 0
        newraw.append(bytes([h[0], h[1], nlen, h[3]]) + cb)
    labels['TOKOFS'] = pos + len(blob); offs = []; tb = b''
    for t in toks: offs.append(len(tb)); tb += t + b'\0'
    blob += struct.pack('<%dH' % max(1, len(offs)), *(offs or [0])); blob += b'\0' * ((-len(blob)) % 4)
    labels['TOKBLOB'] = pos + len(blob); blob += tb; blob += b'\0' * ((-len(blob)) % 4)
    rawmap = dict(zip(keys, newraw))
    strs = [(c, i, rawmap.get((c, i))) for c, i, b in strs]
    print('dictionary: %d tokens, text %d -> %d bytes' % (len(toks), sum(map(len, raws)), sum(map(len, newraw)) + len(tb) + 2 * len(offs)))
    for c, i, b in strs:
        if b is None: continue
        sp = pos + len(blob); blob += b; blob += b'\0' * ((-len(blob)) % 4)
        struct.pack_into('<I', blob, arr[c] - pos + 4 * i, sp)
    labels['SEGEND'] = (pos + len(blob) + 15) & ~15
    assert labels['SEGEND'] <= LIMIT, hex(labels['SEGEND'])
    a.labels.update(labels)
    code = a.build()
    seg = bytearray(64) + code + blob
    struct.pack_into('<i', seg, S_ON, 0)                 # overlay starts hidden; state kept while powered on
    # splice
    img = bytearray(d[0x800:]); need = EXT - T0
    assert len(img) <= need
    img += b'\0' * (need - len(img)) + seg
    img += b'\0' * ((-len(img)) % 2048)
    out = bytearray(d[:0x800]) + img
    struct.pack_into('<I', out, 0x1C, len(img))
    def poke(addr, w): struct.pack_into('<I', out, addr - T0 + 0x800, w)
    poke(HOOK_IN, (2 << 26) | ((a.labels['stubA'] >> 2) & 0x3ffffff)); poke(HOOK_IN + 4, 0)
    assert struct.unpack_from('<I', d, FHOOK - 0x80010200 + 0x800)[0] == 0x3c02800c
    assert struct.unpack_from('<I', d, SHOOK - 0x80010200 + 0x800)[0] == 0x3c02800c
    assert struct.unpack_from('<I', d, SHOOK2 - 0x80010200 + 0x800)[0] == 0x3c02800c
    # vehicle data card: move window (y 18) and its text (y 20) up 14px so tall cards fit on screen
    assert struct.unpack_from('<I', d, 0x80030DDC - 0x80010200 + 0x800)[0] == 0x24060012
    assert struct.unpack_from('<I', d, 0x80030D58 - 0x80010200 + 0x800)[0] == 0x24020014
    poke(0x80030DDC, 0x24060000 | CARDY); poke(0x80030D58, 0x24020000 | (CARDY + 2))
    # monster list 'name' sort: original fills identity (= JP kana record order); use our English A-Z table instead
    assert struct.unpack_from('<I', d, 0x8002974C - 0x80010200 + 0x800)[0] == 0x8f820bfc     # lw v0,3068(gp)
    ns = a.labels['NAMESORT']
    poke(0x8002974C, 0x3c060000 | (((ns >> 16) + (1 if ns & 0x8000 else 0)) & 0xffff))       # lui a2
    poke(0x80029750, 0x24c60000 | (ns & 0xffff))                                             # addiu a2,a2
    poke(0x80029754, (2 << 26) | ((0x800297DC >> 2) & 0x3ffffff)); poke(0x80029758, 0)     # j table-copy path
    # area grid: JP had hardcoded short labels for area 9 and 69 (fixed indices, now wrong after the A-Z re-sort,
    # and the EN copy lacked a terminator). Disable both; MLIST names are short enough now.
    assert struct.unpack_from('<I', d, 0x800299A8 - 0x80010200 + 0x800)[0] == 0x24020009
    assert struct.unpack_from('<I', d, 0x800299B0 - 0x80010200 + 0x800)[0] == 0x24020045
    poke(0x800299A8, 0x2402FFFF); poke(0x800299B0, 0x2402FFFF)
    assert struct.unpack_from('<I', d, 0x8002E124 - 0x80010200 + 0x800)[0] == 0x3c05800c
    assert struct.unpack_from('<I', d, 0x8002E128 - 0x80010200 + 0x800)[0] == 0x24a5b7c4
    se = a.labels['SELEM']
    poke(0x8002E124, 0x3c050000 | (((se >> 16) + (1 if se & 0x8000 else 0)) & 0xffff))
    poke(0x8002E128, 0x24a50000 | (se & 0xffff))
    assert struct.unpack_from('<I', d, 0x8006AD78 - 0x80010200 + 0x800)[0] == 0x240A00B0
    if os.environ.get('KROMHOOK'): poke(0x8006AD78, (2 << 26) | ((a.labels['stubR'] >> 2) & 0x3ffffff)); poke(0x8006AD7C, 0)   # off: had no visible effect
    assert struct.unpack_from('<I', d, 0x80023948 - 0x80010200 + 0x800)[0] == 0x3c02800c
    assert struct.unpack_from('<I', d, 0x8002394C - 0x80010200 + 0x800)[0] == 0x2442ab9c
    ms = a.labels['MASAMUNE']
    poke(0x80023948, 0x3c020000 | (((ms >> 16) + (1 if ms & 0x8000 else 0)) & 0xffff))
    poke(0x8002394C, 0x24420000 | (ms & 0xffff))
    poke(SHOOK2, (2 << 26) | ((a.labels['stubS2'] >> 2) & 0x3ffffff)); poke(SHOOK2 + 4, 0)
    poke(SHOOK, (2 << 26) | ((a.labels['stubS'] >> 2) & 0x3ffffff)); poke(SHOOK + 4, 0)
    poke(FHOOK, (2 << 26) | ((a.labels['stubF'] >> 2) & 0x3ffffff)); poke(FHOOK + 4, 0)
    poke(HOOK_SCHED, (3 << 26) | ((a.labels['stubC'] >> 2) & 0x3ffffff))
    poke(START, (2 << 26) | ((a.labels['clr'] >> 2) & 0x3ffffff)); poke(START + 4, 0)
    # shrink prim buffers: lui a1,hi ; ori a1,a1,lo
    poke(PRIMSZ_PATCH, (0x0f << 26) | (REG['a1'] << 16) | (PRIMSZ >> 16))
    poke(PRIMSZ_PATCH + 4, (0x0d << 26) | (REG['a1'] << 21) | (REG['a1'] << 16) | (PRIMSZ & 0xffff))
    print(f'segment {EXT:#x}..{labels["SEGEND"]:#x} ({labels["SEGEND"]-EXT} bytes, free to {LIMIT:#x}: {LIMIT-labels["SEGEND"]}), '
          f'code {len(code)}, font {sh_w}x{sh_h} @VRAM {FX},{FY} clut {CX},{CY}; {sum(1 for s in strs if s[2])} texts; EXE {len(d)} -> {len(out)}')
    return bytes(out), a.labels

if __name__ == '__main__':
    src, dst, tj = sys.argv[1:4]
    out, _ = build(open(src, 'rb').read(), json.load(open(tj, encoding='utf-8')))
    open(dst, 'wb').write(out)
