"""Minimal R3000 interpreter for testing overlay stubs (no load-delay emulation; we always pad loads with nop)."""
import struct
class CPU:
    def __init__(self, ram):
        self.m = bytearray(ram); self.r = [0] * 32; self.hi = self.lo = 0; self.traps = {}; self.log = []
    def a(self, x): return x & 0x1fffff
    def lw(self, x): assert x % 4 == 0, hex(x); return struct.unpack_from('<I', self.m, self.a(x))[0]
    def sw(self, x, v): assert x % 4 == 0, hex(x); struct.pack_into('<I', self.m, self.a(x), v & 0xffffffff)
    def lh(self, x): return struct.unpack_from('<H', self.m, self.a(x))[0]
    def sh(self, x, v): struct.pack_into('<H', self.m, self.a(x), v & 0xffff)
    def lb(self, x): return self.m[self.a(x)]
    def sb(self, x, v): self.m[self.a(x)] = v & 0xff
    def run(self, pc, stop, maxn=2_000_000):
        r = self.r; npc = pc + 4; n = 0
        while True:
            if pc in stop: return pc
            if pc in self.traps:
                self.traps[pc](self); pc = r[31]; npc = pc + 4; continue
            w = self.lw(pc); n += 1; assert n < maxn, 'runaway'
            op = w >> 26; rs = (w >> 21) & 31; rt = (w >> 16) & 31; rd = (w >> 11) & 31; sa = (w >> 6) & 31; fn = w & 63
            imm = w & 0xffff; simm = imm - 0x10000 if imm & 0x8000 else imm
            nxt = npc + 4; tgt = None
            def S(v): return v - (1 << 32) if v & 0x80000000 else v
            if op == 0:
                if fn == 0x00: v = r[rt] << sa
                elif fn == 0x02: v = r[rt] >> sa
                elif fn == 0x03: v = S(r[rt]) >> sa
                elif fn == 0x08: tgt = r[rs]; v = None
                elif fn == 0x09: tgt = r[rs]; v = npc + 4; rd = rd
                elif fn == 0x21: v = r[rs] + r[rt]
                elif fn == 0x23: v = r[rs] - r[rt]
                elif fn == 0x24: v = r[rs] & r[rt]
                elif fn == 0x25: v = r[rs] | r[rt]
                elif fn == 0x26: v = r[rs] ^ r[rt]
                elif fn == 0x27: v = ~(r[rs] | r[rt])
                elif fn == 0x2a: v = int(S(r[rs]) < S(r[rt]))
                elif fn == 0x2b: v = int(r[rs] < r[rt])
                else: raise Exception('fn %x at %x' % (fn, pc))
                if v is not None and rd: r[rd] = v & 0xffffffff
            elif op == 2: tgt = (pc & 0xf0000000) | ((w & 0x3ffffff) << 2)
            elif op == 3: tgt = (pc & 0xf0000000) | ((w & 0x3ffffff) << 2); r[31] = pc + 8
            elif op == 4: tgt = npc + (simm << 2) if r[rs] == r[rt] else None
            elif op == 5: tgt = npc + (simm << 2) if r[rs] != r[rt] else None
            elif op == 6: tgt = npc + (simm << 2) if S(r[rs]) <= 0 else None
            elif op == 7: tgt = npc + (simm << 2) if S(r[rs]) > 0 else None
            elif op == 1:
                c = S(r[rs]) < 0 if rt == 0 else S(r[rs]) >= 0
                tgt = npc + (simm << 2) if c else None
            elif op == 9: r[rt] = (r[rs] + simm) & 0xffffffff if rt else 0
            elif op == 0x0b: r[rt] = int(r[rs] < (simm & 0xffffffff)) if rt else 0
            elif op == 0x0a: r[rt] = int(S(r[rs]) < simm) if rt else 0
            elif op == 0x0c: r[rt] = r[rs] & imm if rt else 0
            elif op == 0x0d: r[rt] = r[rs] | imm if rt else 0
            elif op == 0x0e: r[rt] = r[rs] ^ imm if rt else 0
            elif op == 0x0f: r[rt] = (imm << 16) if rt else 0
            elif op == 0x23: v = self.lw((r[rs] + simm) & 0xffffffff); r[rt] = v if rt else 0
            elif op == 0x21: v = self.lh((r[rs] + simm) & 0xffffffff); r[rt] = (v - 0x10000 if v & 0x8000 else v) & 0xffffffff if rt else 0
            elif op == 0x25: v = self.lh((r[rs] + simm) & 0xffffffff); r[rt] = v if rt else 0
            elif op == 0x20: v = self.lb((r[rs] + simm) & 0xffffffff); r[rt] = (v - 0x100 if v & 0x80 else v) & 0xffffffff if rt else 0
            elif op == 0x24: v = self.lb((r[rs] + simm) & 0xffffffff); r[rt] = v if rt else 0
            elif op == 0x2b: self.sw((r[rs] + simm) & 0xffffffff, r[rt])
            elif op == 0x29: self.sh((r[rs] + simm) & 0xffffffff, r[rt])
            elif op == 0x28: self.sb((r[rs] + simm) & 0xffffffff, r[rt])
            else: raise Exception('op %x at %x' % (op, pc))
            r[0] = 0
            # delay slot
            if tgt is not None:
                # execute delay slot instruction by stepping once with npc
                dpc = npc
                pc, npc = dpc, tgt
                # run exactly one instruction (the delay slot) then jump
                saved = self.traps; 
                self._one(pc)
                pc = tgt; npc = tgt + 4
            else:
                pc, npc = npc, npc + 4
    def _one(self, pc):
        # execute single non-branch instruction at pc
        stop = {pc + 4}
        self.run(pc, stop)
