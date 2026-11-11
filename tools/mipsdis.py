import struct, sys
R = ['zero','at','v0','v1','a0','a1','a2','a3','t0','t1','t2','t3','t4','t5','t6','t7',
     's0','s1','s2','s3','s4','s5','s6','s7','t8','t9','k0','k1','gp','sp','fp','ra']
I = {0x08:'addi',0x09:'addiu',0x0a:'slti',0x0b:'sltiu',0x0c:'andi',0x0d:'ori',0x0e:'xori',
     0x20:'lb',0x21:'lh',0x23:'lw',0x24:'lbu',0x25:'lhu',0x28:'sb',0x29:'sh',0x2b:'sw',0x22:'lwl',0x26:'lwr'}
SP = {0x00:'sll',0x02:'srl',0x03:'sra',0x04:'sllv',0x06:'srlv',0x07:'srav',0x08:'jr',0x09:'jalr',
      0x10:'mfhi',0x12:'mflo',0x18:'mult',0x19:'multu',0x1a:'div',0x1b:'divu',0x20:'add',0x21:'addu',
      0x22:'sub',0x23:'subu',0x24:'and',0x25:'or',0x26:'xor',0x27:'nor',0x2a:'slt',0x2b:'sltu'}
def dis(w, pc):
    op = w >> 26; rs = (w>>21)&31; rt = (w>>16)&31; rd = (w>>11)&31; sh = (w>>6)&31; fn = w & 63
    imm = w & 0xffff; simm = imm - 0x10000 if imm & 0x8000 else imm
    if w == 0: return 'nop'
    if op == 0:
        n = SP.get(fn, 'sp%02x' % fn)
        if n in ('sll','srl','sra'): return f'{n} {R[rd]},{R[rt]},{sh}'
        if n == 'jr': return f'jr {R[rs]}'
        if n == 'jalr': return f'jalr {R[rs]}'
        if n in ('mfhi','mflo'): return f'{n} {R[rd]}'
        if n in ('mult','multu','div','divu'): return f'{n} {R[rs]},{R[rt]}'
        return f'{n} {R[rd]},{R[rs]},{R[rt]}'
    if op == 1: return f'{"bltz" if rt==0 else "bgez" if rt==1 else "regimm"} {R[rs]},{hex(pc+4+simm*4)}'
    if op in (2,3): return f'{"j" if op==2 else "jal"} {hex((pc & 0xf0000000) | ((w & 0x3ffffff) << 2))}'
    if op in (4,5): return f'{"beq" if op==4 else "bne"} {R[rs]},{R[rt]},{hex(pc+4+simm*4)}'
    if op in (6,7): return f'{"blez" if op==6 else "bgtz"} {R[rs]},{hex(pc+4+simm*4)}'
    if op == 0x0f: return f'lui {R[rt]},{hex(imm)}'
    if op in I:
        n = I[op]
        if op >= 0x20: return f'{n} {R[rt]},{simm}({R[rs]})'
        if n in ('andi','ori','xori'): return f'{n} {R[rt]},{R[rs]},{hex(imm)}'
        return f'{n} {R[rt]},{R[rs]},{simm}'
    return f'op{op:02x} {w:08x}'

if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read(); T = 0x80010200
    a0 = int(sys.argv[2], 16); a1 = int(sys.argv[3], 16)
    for a in range(a0, a1, 4):
        o = a - T + 0x800; w = struct.unpack_from('<I', d, o)[0]
        print(f'{a:08x}: {w:08x}  {dis(w, a)}')
