"""Translate the MAKING OF menu description plates in NPK_MAKE.NPK.
usage: make_build.py <orig NPK_MAKE> <out NPK_MAKE> <preview.png>"""
import sys, os, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '/home/claude/scripts')
import npk, tim

src, dst, prev = sys.argv[1:4]
d = open(src, 'rb').read()
hs = struct.unpack_from('<I', d, 0)[0]
tab = struct.unpack_from(f'<{hs // 4}I', d, 0)
LIMIT = 0x22000
def tim_size(t):
    clen = struct.unpack_from('<I', t, 8)[0]; return 8 + clen + struct.unpack_from('<I', t, 8 + clen)[0]
streams = []; o = hs
for k in range(3):
    hdr, _ = npk.lz_stream_decode(d, o, out_len=4096)
    t, o = npk.lz_stream_decode(d, o, out_len=tim_size(hdr)); streams.append(bytearray(t))
assert o == tab[4] + tab[5]

TEXT = {0: ['Concept art and rough sketches', 'from the making of the game.'],
        1: ['Rare in-development screens and', 'promotional footage.']}
PLATES = {0: (136, 63, 464, 100), 1: (136, 168, 464, 206)}       # interior rects in image-0 coords
# panel textures: image k pixel (u,v) shows image-0 pixel (u+dx, v+dy) in the given v range
# where the game draws each highlight strip (from the GPU commands in a RAM dump: 240x88 sprites at x=8 and x=248)
MAPS = {0: [(0, 240, 0, 0)], 1: [(0, 88, 9, 24), (88, 240, 249, -64)], 2: [(0, 88, 9, 128), (88, 240, 249, 32)]}
# sub-pixel offsets of the JP plate text inside the (resampled) highlight art, measured by template matching;
# the English is sampled at these so it shifts by the same fraction (e.g. MOVIE text rises ~0.12 line when lit)
FRAC = {0: [(0.0, 0.0)], 1: [(8.98, 23.86), (248.93, -64.12)], 2: [(9.01, 128.12), (249.02, 32.12)]}
# offsets follow the highlight ART (matched against the plain panel), so the text moves with the button like the JP disc
HX = float(os.environ.get('HX', '1.6'))
FONT = os.environ.get('MKFONT', '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf')
SIZE = float(os.environ.get('MKSIZE', '11'))
COL = 196; S = 4

def text_layer():
    """alpha (0..1) image in image-0 coords with both plates' text"""
    W, H = 512, 240
    big = Image.new('L', (int(W * S / HX) + 8, H * S), 0); dr = ImageDraw.Draw(big)
    f = ImageFont.truetype(FONT, int(SIZE * S))
    for p, (x0, y0, x1, y1) in PLATES.items():
        lines = TEXT[p]; lh = 15
        for i, ln in enumerate(lines):
            w = dr.textlength(ln, font=f) * HX / S
            assert w <= x1 - x0 - 8, (ln, w)
            dr.text(((x0 + 6) * S / HX, (y0 + 3 + i * lh) * S), ln, fill=255, font=f)
    a = big.resize((W, H), Image.BOX, box=(0, 0, W * S / HX, H * S))
    return np.asarray(a).astype(np.float32) / 255

A = text_layer()
# exact plate shapes (rounded corners): convex hull of the near-black plate in image 0, shrunk by 1 px
import cv2
_p0, _i0, _ = tim.parse(bytes(streams[0])); _img0 = tim.pal_rgb(_p0)[_i0]
PMASK = np.zeros((240, 512), np.uint8)
for p, (x0, y0, x1, y1) in PLATES.items():
    sub = (_img0[y0 - 4:y1 + 5, x0 - 6:x1 + 7].max(2) < 30).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(sub)
    i = 1 + np.argmax(st[1:, 4]); ys, xs = np.where(lab == i)
    hull = cv2.convexHull(np.stack([xs + x0 - 6, ys + y0 - 4], 1).astype(np.int32))
    cv2.fillPoly(PMASK, [hull], 1)
PMASK = cv2.erode(PMASK, np.ones((3, 3), np.uint8)).astype(bool)
for k in range(3):
    t = streams[k]
    pal, idx, off = tim.parse(bytes(t))
    P = tim.pal_rgb(pal)
    img = P[idx].astype(np.float32)
    h, w = idx.shape
    vv, uu = np.mgrid[0:h, 0:w]
    changed = np.zeros((h, w), bool)
    for (v0, v1, dx, dy), (fdx, fdy) in zip(MAPS[k], FRAC[k]):
        for p, (x0, y0, x1, y1) in PLATES.items():
            if p not in {0: (0, 1), 1: (0,), 2: (1,)}[k]: continue
            X = uu + dx; Y = vv + dy
            m = (vv >= v0) & (vv < v1) & (X >= x0) & (X <= x1) & (Y >= y0) & (Y <= y1)
            m &= PMASK[Y.clip(0, 239), X.clip(0, 511)]
            if not m.any(): continue
            # highlighted panels (k>0) are a lit copy: plate black is 8 and the JP text ~1.45x brighter
            pbg, pcol = (0, COL) if k == 0 else (8, min(255, COL * 1.45))
            img[m] = pbg
            ys, xs = np.where(m)
            xf = xs + fdx; yf = ys + fdy                       # bilinear sample of the text layer
            x0i = np.floor(xf).astype(int); y0i = np.floor(yf).astype(int); tx = xf - x0i; ty = yf - y0i
            def g(yy, xx): return A[yy.clip(0, 239), xx.clip(0, 511)]
            a = (g(y0i, x0i) * (1 - tx) * (1 - ty) + g(y0i, x0i + 1) * tx * (1 - ty) +
                 g(y0i + 1, x0i) * (1 - tx) * ty + g(y0i + 1, x0i + 1) * tx * ty)[:, None]
            img[ys, xs] = img[ys, xs] * (1 - a) + pcol * a
            changed |= m
    # never pick the transparent colour (0x0000): black plate pixels must stay opaque or the plain panel shows through
    Pp = P.astype(np.int64).copy(); Pp[np.array(pal) == 0] = 4000      # (int64: a big penalty overflowed int32 before)
    flat = img.clip(0, 255).reshape(-1, 3).astype(np.int64)
    new = ((flat[:, None, :] - Pp[None, :, :]) ** 2).sum(2).argmin(1).astype(np.uint8).reshape(idx.shape)
    idx2 = np.where(changed, new, idx)
    t[off:off + idx2.size] = idx2.astype(np.uint8).tobytes()
    Image.fromarray(P[idx2].astype(np.uint8)).save(prev.replace('.png', f'_{k}.png'))
enc = [npk.encode_stream(bytes(s)) for s in streams]
for k, s in enumerate(streams):
    chk, _ = npk.lz_stream_decode(enc[k], 0, out_len=len(s)); assert chk == bytes(s)
# keep every stream ending exactly where the original ended (the game may decode in place, so the
# compressed bytes must sit where it expects them); the gap before each stream is zero-filled
ends = [tab[0] + tab[1], tab[2] + tab[3], tab[4] + tab[5]]
starts = [hs] + [ends[k] - len(e) for k, e in enumerate(enc)][1:]   # stream 0 stays at the header end (word 0 doubles as header size)
ends[0] = hs + len(enc[0])
assert starts[0] >= hs and all(starts[k] >= ends[k - 1] for k in (1, 2))
print('streams', [len(e) for e in enc], 'starts', starts, 'ends', ends)
out = bytearray(d)
out[hs:LIMIT] = b'\0' * (LIMIT - hs)
for k, e in enumerate(enc): out[starts[k]:ends[k]] = e
newtab = [starts[0], len(enc[0]), starts[1], len(enc[1]), starts[2], len(enc[2])]
struct.pack_into(f'<{hs // 4}I', out, 0, *newtab)
open(dst, 'wb').write(out)
