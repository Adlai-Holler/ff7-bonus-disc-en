"""PSX MDEC STR v2 bitstream: parse (count codes) and encode. Used to re-encode text frames of PP07FF*.STR."""
import numpy as np, struct
AC = {
 '11':(0,1),'011':(1,1),'0100':(0,2),'0101':(2,1),'00101':(0,3),'00111':(3,1),'00110':(4,1),'000110':(1,2),
 '000111':(5,1),'000101':(6,1),'000100':(7,1),'0000110':(0,4),'0000100':(2,2),'0000111':(8,1),'0000101':(9,1),
 '00100110':(0,5),'00100001':(0,6),'00100101':(1,3),'00100100':(3,2),'00100111':(10,1),'00100011':(11,1),
 '00100010':(12,1),'00100000':(13,1),'0000001010':(0,7),'0000001100':(1,4),'0000001011':(2,3),'0000001111':(4,2),
 '0000001001':(5,2),'0000001110':(14,1),'0000001101':(15,1),'0000001000':(16,1),'000000011101':(0,8),
 '000000011000':(0,9),'000000010011':(0,10),'000000010000':(0,11),'000000011011':(1,5),'000000010100':(2,4),
 '000000011100':(3,3),'000000010010':(4,3),'000000011110':(6,2),'000000010101':(7,2),'000000010001':(8,2),
 '000000011111':(17,1),'000000011010':(18,1),'000000011001':(19,1),'000000010111':(20,1),'000000010110':(21,1),
 '0000000011010':(0,12),'0000000011001':(0,13),'0000000011000':(0,14),'0000000010111':(0,15),'0000000010110':(1,6),
 '0000000010101':(1,7),'0000000010100':(2,5),'0000000010011':(3,4),'0000000010010':(5,3),'0000000010001':(9,2),
 '0000000010000':(10,2),'0000000011111':(22,1),'0000000011110':(23,1),'0000000011101':(24,1),'0000000011100':(25,1),
 '0000000011011':(26,1)}
for i, lv in enumerate(range(16, 32)): AC['00000000011' + format(15 - i, '04b')[0:0] + format(0b11111 - i, '05b')[1:]] = None
AC = {k: v for k, v in AC.items() if v}
_l16 = ['00000000011111','00000000011110','00000000011101','00000000011100','00000000011011','00000000011010',
        '00000000011001','00000000011000','00000000010111','00000000010110','00000000010101','00000000010100',
        '00000000010011','00000000010010','00000000010001','00000000010000']
for i, c in enumerate(_l16): AC[c] = (0, 16 + i)
_l32 = ['000000000011000','000000000010111','000000000010110','000000000010101','000000000010100','000000000010011',
        '000000000010010','000000000010001','000000000010000']
for i, c in enumerate(_l32): AC[c] = (0, 32 + i)
_r1 = ['000000000011111','000000000011110','000000000011101','000000000011100','000000000011011','000000000011010','000000000011001']
for i, c in enumerate(_r1): AC[c] = (1, 8 + i)
for c, v in {'0000000000010011':(1,15),'0000000000010010':(1,16),'0000000000010001':(1,17),'0000000000010000':(1,18),
             '0000000000010100':(6,3),'0000000000011010':(11,2),'0000000000011001':(12,2),'0000000000011000':(13,2),
             '0000000000010111':(14,2),'0000000000010110':(15,2),'0000000000010101':(16,2),'0000000000011111':(27,1),
             '0000000000011110':(28,1),'0000000000011101':(29,1),'0000000000011100':(30,1),'0000000000011011':(31,1)}.items():
    AC[c] = v
ENC = {v: k for k, v in AC.items()}
# measured decoder gain per zigzag coefficient at q=1 (orthonormal DCT units per level); = QM[ZZ[i]]/8 roughly
GAIN = [2.0, 2.0321, 2.0321, 2.4152, 1.9795, 2.4152, 2.7457, 2.7457, 2.7457, 2.7457, 2.8, 2.7188, 3.241, 2.9828, 3.2, 3.3506, 3.3506, 3.3981, 3.2306, 3.2087, 3.2087, 3.2309, 3.3665, 3.3615, 3.3665, 3.6769, 3.6577, 3.6769, 4.2317, 4.2014, 4.2014, 3.5874, 3.5874, 3.6711, 3.3981, 3.3506, 3.6577, 3.6385, 3.9418, 4.0, 4.2247, 4.2213, 4.6228, 4.7256, 4.6488, 4.3598, 4.3598, 4.2014, 4.3847, 4.755, 4.7539, 4.9859, 4.9499, 4.9859, 5.9151, 5.9763, 5.7033, 5.7477, 6.969, 7.0355, 7.2132, 8.5861, 8.5861, 10.4163]
AC_SCALE = 8.0
MAXLEN = max(len(k) for k in AC)
ZZ = [0,1,8,16,9,2,3,10,17,24,32,25,18,11,4,5,12,19,26,33,40,48,41,34,27,20,13,6,7,14,21,28,35,42,49,56,57,50,43,36,29,22,15,23,30,37,44,51,58,59,52,45,38,31,39,46,53,60,61,54,47,55,62,63]
QM = [2,16,19,22,26,27,29,34,16,16,22,24,27,29,34,37,19,22,26,27,29,34,34,38,22,22,26,27,29,34,37,40,
      22,26,27,29,32,35,40,48,26,27,29,32,35,40,48,58,26,27,29,34,38,46,56,69,27,29,35,38,46,56,69,83]

class BitReader:
    def __init__(self, b):
        n = len(b) // 2 * 2
        ws = struct.unpack(f'<{n // 2}H', b[:n])
        self.s = ''.join(format(w, '016b') for w in ws); self.p = 0
    def read(self, n): v = self.s[self.p:self.p + n]; self.p += n; return v

def parse(frame, w=320, h=224):
    """returns (qscale, blocks) blocks = list of (dc, [(run, level),...]) in stream order; also code count"""
    cnt, magic, q, ver = struct.unpack_from('<4H', frame, 0)
    assert magic == 0x3800 and ver == 2, (hex(magic), ver)
    br = BitReader(frame[8:]); blocks = []; codes = 0
    nblk = (w // 16) * (h // 16) * 6
    for _ in range(nblk):
        dc = int(br.read(10), 2); dc = dc - 1024 if dc & 512 else dc
        acs = []; codes += 1
        while True:
            if br.s.startswith('10', br.p): br.p += 2; codes += 1; break
            if br.s.startswith('000001', br.p):
                br.p += 6; run = int(br.read(6), 2); lv = int(br.read(10), 2); lv = lv - 1024 if lv & 512 else lv
                acs.append((run, lv)); codes += 1; continue
            for L in range(2, MAXLEN + 1):
                c = br.s[br.p:br.p + L]
                if c in AC:
                    run, lv = AC[c]; br.p += L
                    if br.read(1) == '1': lv = -lv
                    acs.append((run, lv)); codes += 1; break
            else:
                raise ValueError('bad code at bit %d' % br.p)
        blocks.append((dc, acs))
    return q, blocks, codes, cnt, br.p

# ---- forward path
def _dct_mat():
    m = np.zeros((8, 8))
    for k in range(8):
        for n in range(8):
            m[k, n] = (np.sqrt(1 / 8) if k == 0 else np.sqrt(2 / 8)) * np.cos(np.pi * (2 * n + 1) * k / 16)
    return m
D = _dct_mat()
def fdct(b): return D @ b @ D.T

def rgb_to_ycbcr(img):
    img = img.astype(np.float64)
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    y = 0.299 * r + 0.587 * g + 0.114 * b
    cb = -0.168736 * r - 0.331264 * g + 0.5 * b
    cr = 0.5 * r - 0.418688 * g - 0.081312 * b
    return y - 128, cb, cr

def encode_frame(img, q=1):
    """img: HxWx3 uint8 (H,W multiples of 16). returns frame bytes (header + bitstream), code count"""
    H, W = img.shape[:2]
    y, cb, cr = rgb_to_ycbcr(img)
    cb2 = cb.reshape(H // 2, 2, W // 2, 2).mean((1, 3)); cr2 = cr.reshape(H // 2, 2, W // 2, 2).mean((1, 3))
    bits = []; codes = 0
    def block(px):
        nonlocal codes
        c = fdct(px)
        flat = c.flatten()
        # DC: MDEC dc value * qm[0](2) -> coefficient; fdct (orthonormal) dc = 8*mean; mdec idct scale: coef/8 per? use dc = round(c00/ 8)
        dc = int(round(flat[0] / 2)); dc = max(-512, min(511, dc))
        bits.append(format(dc & 1023, '010b')); codes += 1
        run = 0
        for i in range(1, 64):
            v = flat[ZZ[i]]
            lv = int(round(v * 8 / (q * QM[i]) / 2)) if q else 0
            lv = int(round(v / (q * GAIN[i])))
            if lv == 0: run += 1; continue
            lv = max(-512, min(511, lv))
            key = (run, abs(lv))
            if key in ENC: bits.append(ENC[key] + ('1' if lv < 0 else '0'))
            else: bits.append('000001' + format(run, '06b') + format(lv & 1023, '010b'))
            codes += 1; run = 0
        bits.append('10'); codes += 1
    for mx in range(W // 16):
        for my in range(H // 16):
            ys, xs = my * 16, mx * 16
            block(cr2[ys // 2:ys // 2 + 8, xs // 2:xs // 2 + 8]); block(cb2[ys // 2:ys // 2 + 8, xs // 2:xs // 2 + 8])
            block(y[ys:ys + 8, xs:xs + 8]); block(y[ys:ys + 8, xs + 8:xs + 16])
            block(y[ys + 8:ys + 16, xs:xs + 8]); block(y[ys + 8:ys + 16, xs + 8:xs + 16])
    s = ''.join(bits)
    s += '0' * ((-len(s)) % 32)
    words = [int(s[i:i + 16], 2) for i in range(0, len(s), 16)]
    body = struct.pack(f'<{len(words)}H', *words)
    cnt = ((codes + 1) // 2 + 31) & ~31
    return struct.pack('<4H', cnt, 0x3800, q, 2) + body, codes

def encode_levels(blocks, q=1):
    """blocks: list (stream order) of (dc, {zigzag_index: level}) -> frame bytes"""
    bits = []; codes = 0
    for dc, lv in blocks:
        bits.append(format(dc & 1023, '010b')); codes += 1; run = 0
        for i in range(1, 64):
            l = lv.get(i, 0)
            if l == 0: run += 1; continue
            key = (run, abs(l))
            bits.append(ENC[key] + ('1' if l < 0 else '0') if key in ENC else '000001' + format(run, '06b') + format(l & 1023, '010b'))
            codes += 1; run = 0
        bits.append('10'); codes += 1
    s = ''.join(bits); s += '0' * ((-len(s)) % 32)
    words = [int(s[i:i + 16], 2) for i in range(0, len(s), 16)]
    cnt = ((codes + 1) // 2 + 31) & ~31
    return struct.pack('<4H', cnt, 0x3800, q, 2) + struct.pack(f'<{len(words)}H', *words)
