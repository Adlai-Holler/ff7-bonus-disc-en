"""LPK/NPK block-chain LZSS codec used by the FF7 Perfect Guide disc."""
import struct

import ctypes as _ct, os as _os
_LIB = None
def _lib():
    global _LIB
    if _LIB is None:
        p = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'c', 'liblzmatch.so')
        _LIB = _ct.CDLL(p) if _os.path.exists(p) else False
    return _LIB
def _fast_parse(data, cands_max=512):
    """C match finder + optimal parse; returns (ml, mp, choice) lists, or None if the library is missing."""
    lib = _lib()
    if not lib: return None
    import numpy as _np
    n = len(data); buf = _np.frombuffer(bytes(data), _np.uint8)
    ml = _np.zeros(n, _np.int32); mp = _np.zeros(n, _np.int32); ch = _np.zeros(n, _np.int32)
    P = _ct.POINTER(_ct.c_int32)
    lib.find_matches(buf.ctypes.data_as(_ct.c_void_p), n, cands_max, ml.ctypes.data_as(P), mp.ctypes.data_as(P))
    lib.parse(ml.ctypes.data_as(P), n, ch.ctypes.data_as(P))
    return ml.tolist(), mp.tolist(), ch.tolist()
def items(d):
    o = 0; out = []
    while o + 8 <= len(d):
        if d[o:o+8] == b'\0' * 8: o += 2048; continue
        n = struct.unpack_from('<I', d, o)[0]
        if not 0 < n < 4000: break
        out.append((o, n)); o += ((n * 1024 + 2047) // 2048) * 2048
    return out
def decode(d, o, trace=False):
    n = struct.unpack_from('<I', d, o)[0]; blocks = []
    stream = bytearray(); bounds = []
    for k in range(n):
        b = o + k * 1024; rem, end, dec = struct.unpack_from('<IHH', d, b)
        bounds.append((len(stream), len(stream) + end - 8, dec)); stream += d[b+8:b+end]
    ring = bytearray(4096); w = 4078; out = bytearray(); p = 0; total = sum(x[2] for x in bounds)
    events = []   # (stream_pos_after_flagbyte_or_token, out_len)
    while len(out) < total and p < len(stream):
        fp = p; flags = stream[p]; p += 1
        for bit in range(8):
            if len(out) >= total or p >= len(stream): break
            if flags >> bit & 1:
                c = stream[p]; p += 1; out.append(c); ring[w] = c; w = (w + 1) & 4095
            else:
                b0, b1 = stream[p], stream[p+1]; p += 2
                pos = b0 | ((b1 & 0xf0) << 4); ln = (b1 & 0xf) + 3
                for i in range(ln):
                    c = ring[(pos + i) & 4095]; out.append(c); ring[w] = c; w = (w + 1) & 4095
            events.append((p, len(out)))
    return bytes(out), bounds, events

def game_decode(d, o):
    """Exact reimplementation of the game's per-block decompressor (0x80058A40)."""
    n = struct.unpack_from('<I', d, o)[0]; out = bytearray()
    for k in range(n):
        b = o + k * 1024; rem, end, dec = struct.unpack_from('<IHH', d, b)
        s = d[b+8:b+end]; p = 0; flags = 0
        while p < len(s):
            flags >>= 1
            if not flags & 0x100: flags = s[p] | 0xff00; p += 1
            if flags & 1: out.append(s[p]); p += 1
            else:
                b0, b1 = s[p], s[p+1]; p += 2; pos = b0 | ((b1 & 0xf0) << 4); ln = (b1 & 0xf) + 3
                v1 = len(out) + 4078; v0 = (v1 & ~0xfff) + pos
                if not v0 < v1: v0 -= 4096
                src = v0 - 4078
                for i in range(ln): out.append(out[src + i] if src + i >= 0 else 0)
    return bytes(out)

def encode(data, block=1024, maxs=None, cands_max=512, lazy=True):
    """Encode `data` into a block chain the game's decompressor accepts.
    Each block: u32 blocks-remaining, u16 end (bytes used incl. 8-byte header), u16 bytes produced,
    then a stream that starts a fresh flag byte. Window 4096, match length 3..18.
    Blocks are filled to the last token that fits (a flag group may be cut short; the decoder stops at `end`)."""
    MAXS = maxs or (block - 8)
    from collections import defaultdict
    heads = defaultdict(list)
    N = len(data)
    def best_match(i):
        if i + 3 > N: return 0, 0
        cands = heads.get(data[i:i+3], ())
        bl = 0; bp = 0; lim = min(18, N - i)
        for j in reversed(cands[-cands_max:]):
            if i - j > 4095 - 18: break
            l = 3
            while l < lim and data[j + l] == data[i + l]: l += 1
            if l > bl: bl, bp = l, j
            if l == lim: break
        return bl, bp
    def add(i):
        if i + 3 <= N: heads[data[i:i+3]].append(i)
    blocks = []; i = 0
    while i < N:
        s = bytearray(); start = i
        while i < N and len(s) + 2 <= MAXS:          # need room for a flag byte + at least one literal
            fpos = len(s); s.append(0); flags = 0
            for bit in range(8):
                if i >= N: break
                room = MAXS - len(s)
                l, j = best_match(i)
                if lazy and l >= 3 and l < 18:
                    l2, _ = best_match(i + 1)
                    if l2 > l + 1: l = 0                  # emit a literal, take the longer match next
                if l >= 3 and room >= 2:
                    pos = (j + 4078) & 0xfff
                    s += bytes([pos & 0xff, ((pos >> 4) & 0xf0) | (l - 3)])
                    for k in range(l): add(i + k)
                    i += l
                elif room >= 1:
                    flags |= 1 << bit; s.append(data[i]); add(i); i += 1
                else:
                    break
            s[fpos] = flags
        blocks.append((s, i - start))
    out = bytearray(); n = len(blocks)
    for k, (s, produced) in enumerate(blocks):
        hdr = struct.pack('<IHH', n - k, len(s) + 8, min(produced, 0xffff))
        out += hdr + s + b'\0' * (block - 8 - len(s))
    return bytes(out), n

def encode_blocks(data, target):
    """Encode so the chain has exactly `target` blocks (the loader checks (n+1)//2 == item sectors)."""
    lo, hi = 64, 1016
    enc, n = encode_opt(data)
    if n == target: return enc
    if n == target + 1 and target % 2 == 1: return enc   # same sector count ((n+1)//2)
    if n > target: raise ValueError(f'needs {n} blocks > {target}')
    # shrink per-block stream budget until block count reaches target
    while lo < hi:
        mid = (lo + hi + 1) // 2
        e, k = encode_opt(data, maxs=mid)
        if k >= target: lo = mid
        else: hi = mid - 1
    e, k = encode_opt(data, maxs=lo)
    if k != target:
        # fine-tune downward one byte at a time
        m = lo
        while k != target and m > 64:
            m -= 1; e, k = encode_opt(data, maxs=m)
    assert k == target, (k, target)
    return e

def encode_opt(data, block=1024, maxs=None, cands_max=512):
    """Optimal-parse LZSS (min literal/match bit cost), packed into the game's block chain."""
    MAXS = maxs or (block - 8)
    N = len(data)
    fast = _fast_parse(data, cands_max)
    if fast: ml, mp, choice = fast
    else:
        from collections import defaultdict
        N = len(data)
        heads = defaultdict(list)
        ml = [0] * N; mp = [0] * N
        for i in range(N):
            if i + 3 <= N:
                cands = heads[data[i:i+3]]
                bl = 0; bp = 0; lim = min(18, N - i)
                for j in reversed(cands[-cands_max:]):
                    if i - j > 4095 - 18: break
                    l = 3
                    while l < lim and data[j + l] == data[i + l]: l += 1
                    if l > bl: bl, bp = l, j
                    if l == lim: break
                ml[i] = bl; mp[i] = bp
                cands.append(i)
        INF = 1 << 60
        cost = [0] * (N + 1); choice = [0] * N
        for i in range(N - 1, -1, -1):
            best = 9 + cost[i + 1]; ch = 1
            for l in range(3, ml[i] + 1):
                c = 17 + cost[i + l]
                if c < best: best = c; ch = l
            cost[i] = best; choice[i] = ch
    toks = []; i = 0
    while i < N:
        l = choice[i]
        if l >= 3: toks.append((l, mp[i])); i += l
        else: toks.append((1, data[i])); i += 1
    blocks = []; t = 0; pos = 0
    while t < len(toks):
        s = bytearray(); start = pos
        while t < len(toks) and len(s) + 1 + (2 if toks[t][0] >= 3 else 1) <= MAXS:
            fpos = len(s); s.append(0); flags = 0
            for bit in range(8):
                if t >= len(toks): break
                l, v = toks[t]; room = MAXS - len(s)
                if l >= 3:
                    if room < 2: break
                    p = (v + 4078) & 0xfff
                    s += bytes([p & 0xff, ((p >> 4) & 0xf0) | (l - 3)]); pos += l
                else:
                    if room < 1: break
                    flags |= 1 << bit; s.append(v); pos += 1
                t += 1
            s[fpos] = flags
        blocks.append((s, pos - start))
    out = bytearray(); n = len(blocks)
    for k, (s, produced) in enumerate(blocks):
        out += struct.pack('<IHH', n - k, len(s) + 8, min(produced, 0xffff)) + s + b'\0' * (block - 8 - len(s))
    return bytes(out), n

def lz_stream_decode(d, o, out_len=None, end=None):
    """Continuous LZSS stream (flags LSB-first, 1=literal; 12-bit ring pos, len 3..18), no block headers.
    Stops at out_len output bytes or at input offset `end`. Returns (bytes, input_end_offset)."""
    out = bytearray(); p = o; flags = 0
    while (out_len is None or len(out) < out_len) and (end is None or p < end) and p < len(d):
        flags >>= 1
        if not flags & 0x100: flags = d[p] | 0xff00; p += 1
        if (end is not None and p >= end) or p >= len(d): break
        if flags & 1: out.append(d[p]); p += 1
        else:
            b0, b1 = d[p], d[p+1]; p += 2
            pos = b0 | ((b1 & 0xf0) << 4); ln = (b1 & 0xf) + 3
            v1 = len(out) + 4078; v0 = (v1 & ~0xfff) + pos
            if not v0 < v1: v0 -= 4096
            src = v0 - 4078
            for k in range(ln): out.append(out[src + k] if src + k >= 0 else 0)
    return bytes(out), p

def encode_stream(data, cands_max=512):
    """Optimal-parse LZSS as one continuous stream (for NPK_DF/NPK_MAIN style containers)."""
    N = len(data)
    fast = _fast_parse(data, cands_max)
    if fast: ml, mp, choice = fast
    else:
        from collections import defaultdict
        N = len(data); heads = defaultdict(list)
        ml = [0] * N; mp = [0] * N
        for i in range(N):
            if i + 3 <= N:
                cands = heads[data[i:i+3]]; bl = 0; bp = 0; lim = min(18, N - i)
                for j in reversed(cands[-cands_max:]):
                    if i - j > 4095 - 18: break
                    l = 3
                    while l < lim and data[j + l] == data[i + l]: l += 1
                    if l > bl: bl, bp = l, j
                    if l == lim: break
                ml[i] = bl; mp[i] = bp; cands.append(i)
        cost = [0] * (N + 1); choice = [1] * N
        for i in range(N - 1, -1, -1):
            best = 9 + cost[i + 1]; ch = 1
            for l in range(3, ml[i] + 1):
                c = 17 + cost[i + l]
                if c < best: best = c; ch = l
            cost[i] = best; choice[i] = ch
    out = bytearray(); i = 0
    while i < N:
        fpos = len(out); out.append(0); flags = 0
        for bit in range(8):
            if i >= N: break
            l = choice[i]
            if l >= 3:
                p = (mp[i] + 4078) & 0xfff
                out += bytes([p & 0xff, ((p >> 4) & 0xf0) | (l - 3)]); i += l
            else:
                flags |= 1 << bit; out.append(data[i]); i += 1
        out[fpos] = flags
    return bytes(out)

def chain_blocks(d, o):
    """[(block_offset, bytes_actually_decoded)] for a block chain at d[o].
    The header's 'produced' field is not reliable in the original files, so decode to measure."""
    n = struct.unpack_from('<I', d, o)[0]; res = []
    out = bytearray()
    for k in range(n):
        before = len(out); _decode_block(d, o + k * 1024, out); res.append((o + k * 1024, len(out) - before))
    return res

def _decode_block(d, b, out):
    rem, end, dec = struct.unpack_from('<IHH', d, b)
    s = d[b+8:b+end]; p = 0; flags = 0
    while p < len(s):
        flags >>= 1
        if not flags & 0x100: flags = s[p] | 0xff00; p += 1
        if p >= len(s): break
        if flags & 1: out.append(s[p]); p += 1
        else:
            b0, b1 = s[p], s[p+1]; p += 2; pos = b0 | ((b1 & 0xf0) << 4); ln = (b1 & 0xf) + 3
            v1 = len(out) + 4078; v0 = (v1 & ~0xfff) + pos
            if not v0 < v1: v0 -= 4096
            src = v0 - 4078
            for i in range(ln): out.append(out[src + i] if src + i >= 0 else 0)

def game_decode_n(d, o, nblocks):
    """game_decode limited to the first `nblocks` blocks of the chain."""
    out = bytearray()
    for k in range(nblocks): _decode_block(d, o + k * 1024, out)
    return bytes(out)

def encode_tail(data, P, nblocks_left, cands_max=512, block=1024):
    """Encode data[P:] as `nblocks_left` blocks that continue a chain whose earlier blocks produced data[:P].
    Matches may reach back into data[:P] (the decoder's ring buffer already holds it). Returns bytes."""
    fast = _fast_parse(data, cands_max)
    assert fast, 'C match finder required'
    ml, mp, choice = fast
    toks = []; i = P
    while i < len(data):
        l = choice[i]
        if l >= 3: toks.append((l, mp[i])); i += l
        else: toks.append((1, data[i])); i += 1
    def pack(maxs):
        blocks = []; t = 0
        while t < len(toks):
            s = bytearray(); produced = 0
            while t < len(toks) and len(s) + 1 + (2 if toks[t][0] >= 3 else 1) <= maxs:
                fpos = len(s); s.append(0); flags = 0
                for bit in range(8):
                    if t >= len(toks): break
                    l, v = toks[t]; room = maxs - len(s)
                    if l >= 3:
                        if room < 2: break
                        p = (v + 4078) & 0xfff
                        s += bytes([p & 0xff, ((p >> 4) & 0xf0) | (l - 3)]); produced += l
                    else:
                        if room < 1: break
                        flags |= 1 << bit; s.append(v); produced += 1
                    t += 1
                s[fpos] = flags
            blocks.append((s, produced))
        return blocks
    lo, hi = 16, block - 8
    blocks = pack(hi)
    if len(blocks) > nblocks_left: raise ValueError(f'tail needs {len(blocks)} blocks > {nblocks_left}')
    if len(blocks) < nblocks_left:              # spread over exactly nblocks_left blocks
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if len(pack(mid)) >= nblocks_left: lo = mid
            else: hi = mid - 1
        blocks = pack(lo)
        assert len(blocks) == nblocks_left, (len(blocks), nblocks_left)
    out = bytearray()
    for k, (s, produced) in enumerate(blocks):
        out += struct.pack('<IHH', nblocks_left - k, len(s) + 8, min(produced, 0xffff)) + s + b'\0' * (block - 8 - len(s))
    return bytes(out)
