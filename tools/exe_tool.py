#!/usr/bin/env python3
"""FF7 Perfect Guide SLPS_010.60 text tool.

extract EXE out.tsv          -> every NUL-terminated string containing Japanese text
insert  EXE in.tsv OUT_EXE   -> write column 'en' back in place (same slot, never grows)

Escapes used in the tsv:
  \\n      newline (0x0A)
  {~fXX}  control code 7E 66 XX
  {XX}    any other control byte
Slot = original string bytes + the zero padding after it (minus 1 for the terminator),
so a translation can never overwrite the next string.
"""
import sys, csv

def is_lead(b): return 0x81 <= b <= 0x9f or 0xe0 <= b <= 0xfc

def decode(seg):
    out = []; i = 0; sj = 0; bad = 0
    while i < len(seg):
        b = seg[i]
        if b == 0x7e and i + 2 < len(seg) + 0 and i + 2 <= len(seg) - 1 and seg[i+1] == 0x66:
            out.append('{~f%02X}' % seg[i+2]); i += 3; continue
        if b == 0x0a: out.append('\\n'); i += 1; continue
        if b < 0x20 or b == 0x7f: out.append('{%02X}' % b); bad += 1; i += 1; continue
        if is_lead(b) and i + 1 < len(seg):
            try:
                c = seg[i:i+2].decode('cp932'); out.append(c); sj += 1; i += 2; continue
            except UnicodeDecodeError:
                return None
        if 0xa1 <= b <= 0xdf:  # half-width katakana
            out.append(seg[i:i+1].decode('cp932')); i += 1; continue
        if b < 0x80: out.append(chr(b)); i += 1; continue
        return None
    return ''.join(out), sj, bad

def encode(s):
    out = bytearray(); i = 0
    while i < len(s):
        if s.startswith('\\n', i): out.append(0x0a); i += 2; continue
        if s.startswith('{~f', i):
            out += bytes([0x7e, 0x66, int(s[i+3:i+5], 16)]); i += 6; continue
        if s[i] == '{' and i + 3 < len(s) and s[i+3] == '}':
            out.append(int(s[i+1:i+3], 16)); i += 4; continue
        out += s[i].encode('cp932'); i += 1
    return bytes(out)

def plausible(text, sj, bad):
    if sj == 0: return False
    if bad > 2: return False
    jp = sum(1 for c in text if '぀' <= c <= 'ヿ' or c in '　、。・ー！？（）「」：＆')
    return sj >= 2 and jp / sj >= 0.25 or (sj >= 1 and jp == sj)

def read_tsv(p):
    lines = open(p, encoding='utf-8').read().split('\n')
    head = lines[0].split('\t')
    for l in lines[1:]:
        if l.strip(): yield dict(zip(head, l.split('\t') + [''] * len(head)))

def extract(exe, tsv):
    d = open(exe, 'rb').read()
    rows = []; i = 0; n = len(d)
    while i < n:
        if d[i] == 0: i += 1; continue
        j = d.find(b'\0', i)
        if j < 0: j = n
        seg = d[i:j]
        r = decode(seg)
        if r and plausible(*r):
            k = j
            while k < n and d[k] == 0: k += 1
            slot = (k - i) - 1          # bytes usable before a terminator is required
            rows.append((i, len(seg), slot, r[0]))
        i = j + 1
    with open(tsv, 'w', encoding='utf-8') as f:
        f.write('offset\tjplen\tslot\tjp\ten\tnote\n')
        for o, l, s, t in rows: f.write(f'{o:06X}\t{l}\t{s}\t{t}\t\t\n')
    print(f'{len(rows)} strings -> {tsv}')

def code_refs(d):
    """addresses built with lui/addiu (or lw/lh/lb) pairs in the code area"""
    import struct
    refs = set()
    for i in range(0x800, 0x70000, 4):
        w = struct.unpack_from('<I', d, i)[0]; op = w >> 26
        if op in (0x09, 0x23, 0x21, 0x25, 0x20, 0x24):
            imm = w & 0xffff; simm = imm - 0x10000 if imm & 0x8000 else imm; rs = (w >> 21) & 31
            for k in range(1, 16):
                j = i - 4 * k
                if j < 0x800: break
                w2 = struct.unpack_from('<I', d, j)[0]
                if w2 >> 26 == 0x0f and (w2 >> 16) & 31 == rs:
                    refs.add((((w2 & 0xffff) << 16) + simm) & 0xffffffff); break
    return refs

def find_ptrs(d, o):
    import struct
    t_addr = struct.unpack_from('<I', d, 0x18)[0]
    p = struct.pack('<I', t_addr + o - 0x800); hits = []; i = d.find(p)
    while i >= 0:
        if i % 4 == 0: hits.append(i)
        i = d.find(p, i + 1)
    return hits, t_addr

def insert(exe, tsv, out, verbose='0'):
    """Non-label strings: in place (relocated if needed). Movable label strings: freed, then repacked
    (deduplicated); English is used for as many as the free space allows, the rest keep their Japanese."""
    import struct, sys
    sys.path.insert(0, '/home/claude/scripts'); import labelenc as L
    orig = open(exe, 'rb').read(); d = bytearray(orig)
    t_addr = struct.unpack_from('<I', orig, 0x18)[0]
    A = lambda o: t_addr + o - 0x800
    crefs = code_refs(orig)
    free = []; items = []; fails = []
    for r in read_tsv(tsv):
        o = int(r['offset'], 16); slot = int(r['slot']); en = r.get('en', '')
        src = bytes(orig[o:o+int(r['jplen'])])
        if r['jp'].startswith('crc32:'):   # published tables carry a checksum instead of the original Japanese text
            import zlib; assert '%08x' % zlib.crc32(src) == r['jp'][6:], f'mismatch @{r["offset"]}'
            r['jp'] = decode(src)[0]          # recovered from your own disc's EXE
        else: assert decode(src)[0] == r['jp'], f'mismatch @{r["offset"]}'
        slot = min(slot, ((o + int(r['jplen']) + 1 + 3) & ~3) - o - 1)   # own bytes + alignment only
        gpzone = 0xA3330 <= o < 0xB3330                                   # gp-relative .sdata: never reuse
        lab = L.is_label(o)
        if en and lab: b = encode(L.encode_ascii(en, 26))
        elif en and L.is_text(o): b = encode(L.encode_ascii(en, 28))
        else:
            if en and 0x70000 <= o < 0x75000 and '\\n' in r['jp']:
                jl = [len(encode(x)) for x in r['jp'].split('\\n')]
                el = en.split('\\n')
                el = [x + ' ' * max(0, jl[i] - len(encode(x))) if i < len(jl) else x for i, x in enumerate(el)]
                en = '\\n'.join(el)
            b = encode(en) if en else None
        hits = find_ptrs(orig, o)[0]
        movable = bool(hits) and A(o) not in crefs
        jpb = bytes(orig[o:o+int(r['jplen'])])
        if lab and movable and not gpzone:
            free.append([o, o + slot + 1]); items.append({'r': r, 'hits': hits, 'jp': jpb, 'en': b, 'use_en': False}); continue
        if gpzone:
            if b is None: continue
            if len(b) <= slot: d[o:o+slot+1] = b + b'\0' * (slot + 1 - len(b)); continue
            if movable:
                items.append({'r': r, 'hits': hits, 'jp': jpb, 'en': b, 'use_en': True, 'must': True}); continue
            fails.append((r['offset'], slot, len(b), en, 'no pointer')); continue
        if b is None: continue
        if len(b) <= slot:
            d[o:o+slot+1] = b + b'\0' * (slot + 1 - len(b))
            if slot - len(b) >= 4 and L.is_text(o): free.append([o + len(b) + 1, o + slot + 1])
        elif movable:
            free.append([o, o + slot + 1]); items.append({'r': r, 'hits': hits, 'jp': jpb, 'en': b, 'use_en': True, 'must': True})
        else:
            fails.append((r['offset'], slot, len(b), en, 'no pointer'))
    free.sort(); merged = []
    for a, b2 in free:
        if merged and a <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], b2)
        else: merged.append([a, b2])
    import asmpatch
    big = max(merged, key=lambda m: m[1] - m[0])
    cave = (big[0] + 3) & ~3; big[0] = cave + asmpatch.CAVE_SIZE
    total = sum(b2 - a for a, b2 in merged)
    def cost(its):
        seen = set(); c = 0
        for it in its:
            x = it['en'] if it['use_en'] else it['jp']
            if x not in seen: seen.add(x); c += len(x) + 4
        return c
    budget = total * float(__import__("os").environ.get("LBUDGET", "0.99"))
    if verbose != '0':
        for it in items: it['use_en'] = bool(it.get('must'))
        cj = cost(items)
        for it in items: it['use_en'] = it['en'] is not None
        ce = cost(items)
        for it in items: it['use_en'] = bool(it.get('must'))
        mu = sum(len(it['en']) for it in items if it.get('must'))
        print(f'free {total}  cost all-JP {cj}  cost all-EN {ce}  must items {sum(1 for it in items if it.get("must"))} ({mu} bytes)  blocks {len(merged)} largest {max(b2-a for a,b2 in merged)}')
    for it in items: it['use_en'] = it['en'] is not None
    worst = sorted([it for it in items if it['use_en'] and not it.get('must') and len(it['en']) > len(it['jp'])],
                   key=lambda it: len(it['jp']) - len(it['en']))
    while cost(items) > budget and worst: worst.pop(0)['use_en'] = False
    def allocate():
        blocks = [list(m) for m in merged]; groups = {}
        for it in items: groups.setdefault(it['en'] if it['use_en'] else it['jp'], []).append(it)
        plan = []
        for data in sorted(groups, key=len, reverse=True):
            need = len(data) + 1; best = None
            for blk in blocks:
                a = (blk[0] + 3) & ~3
                if blk[1] - a >= need and (best is None or blk[1] - blk[0] < best[1] - best[0]): best = blk
            if best is None: return None, groups[data]
            a = (best[0] + 3) & ~3; best[0] = a + need; plan.append((a, data, groups[data]))
        return plan, blocks
    for _ in range(2000):
        plan, extra = allocate()
        if plan is not None: break
        down = [it for it in extra if it['use_en'] and not it.get('must')]
        if not down:
            down = sorted([it for it in items if it['use_en'] and not it.get('must')], key=lambda it: len(it['jp']) - len(it['en']))[:1]
        for it in down: it['use_en'] = False
    for a, b2 in merged: d[a:b2] = b'\0' * (b2 - a)
    for a, data, its in plan:
        d[a:a+len(data)+1] = data + b'\0'
        for it in its:
            for h in it['hits']: struct.pack_into('<I', d, h, A(a))
    asmpatch.apply(d, cave)
    open(out, 'wb').write(d)
    en_n = sum(1 for it in items if it['use_en']); tr_n = sum(1 for it in items if it['en'] is not None)
    spare = sum(b2 - a for a, b2 in extra)
    for f in fails: print('FAILED @%s slot %d need %d (%s): %s' % (f[0], f[1], f[2], f[4], f[3][:50]))
    print(f'labels: {en_n} of {tr_n} translated labels in English, {tr_n - en_n} kept Japanese for space; spare {spare} bytes -> {out}')
    return len(fails)

if __name__ == '__main__':
    {'extract': extract, 'insert': insert}[sys.argv[1]](*sys.argv[2:])
