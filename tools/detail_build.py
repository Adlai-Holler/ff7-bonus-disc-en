"""Translate the caption bars of the close-up ("detail") pictures in TOWN/FF_TTOWN.NPK.
usage: detail_build.py <in FF_TTOWN.NPK> <out FF_TTOWN.NPK> <preview_dir> <captions.json>
captions.json: {"<detail index>": "Caption\\nsecond line", ...}  (index = order in the container scan, see list.pkl)"""
import sys, os, struct, json, pickle
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
sys.path.insert(0, '/home/claude/scripts')
import npk

src, dst, prev, capf = sys.argv[1:5]
d = bytearray(open(src, 'rb').read())
caps = {int(k): v for k, v in json.load(open(capf, encoding='utf-8')).items()}
os.makedirs(prev, exist_ok=True)
FONT = os.environ.get('DFONT', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
SIZE = float(os.environ.get('DSIZE', '12'))
XS = float(os.environ.get('DXS', '1.25'))     # horizontal stretch: pixels are narrow on a 4:3 TV
SHADOW = os.environ.get('DSHADOW', '1') == '1'
NOTESIZE, NOTEPITCH = 8.5, 10
PITCH = float(os.environ.get('DPITCH', '12'))
S = 4
NAVY = np.array([0, 16, 88]); INK = np.array([int(x) for x in os.environ.get('DINK', '208,208,208').split(',')])
B = 4                      # border thickness around the navy field

info = pickle.load(open('/home/claude/npk/town/tt_info.pkl', 'rb'))
covered = set()
for k, o, n, w, h, pm in info:
    covered.update(range(o // 2048, (o + n * 1024 + 2047) // 2048))

def containers():
    """detail containers in file order: (offset, [(start, size)...])"""
    out = []; s = 0; N = len(d) // 2048
    while s < N:
        o = s * 2048
        if s in covered or d[o:o + 8] == b'\0' * 8: s += 1; continue
        hs, s0 = struct.unpack_from('<2I', d, o)
        if hs % 8 == 0 and 8 <= hs <= 200 and s0 != 64:
            ents = [struct.unpack_from('<2I', d, o + 8 * i) for i in range(hs // 8)]
            out.append((o, ents))
        s += 1
        while s < N and s not in covered and d[s * 2048:s * 2048 + 16] != b'\0' * 16 \
                and struct.unpack_from('<I', d, s * 2048)[0] > 4000: s += 1
    return out

def tim_len(t):
    cl = struct.unpack_from('<I', t, 8)[0]; return 8 + cl + struct.unpack_from('<I', t, 8 + cl)[0]

def tim_parts(t):
    cl = struct.unpack_from('<I', t, 8)[0]
    pal = np.frombuffer(bytes(t), '<u2', count=256, offset=20)
    o = 8 + cl; w2, h = struct.unpack_from('<HH', t, o + 8); w = w2 * 2
    return pal, o + 12, w, h

def pal_rgb(pal):
    return np.stack([(pal & 31) << 3, ((pal >> 5) & 31) << 3, ((pal >> 10) & 31) << 3], -1).astype(int)

def find_box(a):
    h = a.shape[0]
    m = (np.abs(a - NAVY).max(2) <= int(os.environ.get('NAVYTOL', '8'))); m[:h // 3] = False
    lab, n = ndimage.label(m)
    if n == 0: return None
    sz = ndimage.sum(m, lab, range(1, n + 1)); k = int(np.argmax(sz)) + 1
    if sz[k - 1] < 300: return None
    ys, xs = np.where(lab == k)
    return xs.min(), ys.min(), xs.max(), ys.max()

def wrap_balanced(text, f, n):
    words = text.replace('\n', ' ').split(' ')
    best = None
    import itertools
    for cuts in itertools.combinations(range(1, len(words)), n - 1):
        parts = [' '.join(words[i:j]) for i, j in zip((0,) + cuts, cuts + (len(words),))]
        wmax = max(f.getlength(p) for p in parts)
        if best is None or wmax < best[0]: best = (wmax, parts)
    return best[1] if best else [text]

def layout(text, maxw):
    """original look: ~12px glyphs on a 12px line pitch; wrap (balanced) before shrinking"""
    for size in np.arange(SIZE, 8.0, -0.5):
        f = ImageFont.truetype(FONT, int(size * S))
        lines = text.split('\n')
        if all(f.getlength(l) * XS / S <= maxw for l in lines): return f, size, lines
        nw = len(text.replace('\n', ' ').split(' '))
        for n in range(len(lines) + 1, min(4, nw) + 1):
            ls = wrap_balanced(text, f, n)
            if all(f.getlength(l) * XS / S <= maxw for l in ls): return f, size, ls
    return f, size, lines

def process(t, text, name):
    pal, po, W, H = tim_parts(t)
    idx = np.frombuffer(bytes(t), np.uint8, count=W * H, offset=po).reshape(H, W).copy()
    P = pal_rgb(pal); a = P[idx]
    fb = find_box(a)
    if fb is None: print('  no caption box found in', name, '- skipped'); return bytes(t), None
    x0, y0, x1, y1 = fb
    ox0, oy0, ox1, oy1 = x0 - B, y0 - B, x1 + B, y1 + B          # outer box incl. border
    PADX, PADT, PADB = 9, 2, 3
    maxw = W - 2 * B - 2
    note = None
    if '\n~' in text: text, note = text.split('\n~', 1)       # '~' line: small translator's note under the name
    f, size, lines = layout(text, maxw - 2 * PADX)
    lh = PITCH
    tw = max(f.getlength(l) for l in lines) * XS / S; th = lh * len(lines)
    if note:
        fn = ImageFont.truetype(FONT, int(NOTESIZE * S)); tw = max(tw, fn.getlength(note) * XS / S); th += NOTEPITCH
    inner_w = x1 - x0 + 1; inner_h = y1 - y0 + 1
    assert int(np.ceil(tw)) + 2 * PADX <= maxw, ('caption too wide', name, text, note)
    nw = int(np.ceil(tw)) + 2 * PADX; nh = int(round(th)) + PADT + PADB
    cx = (x0 + x1) / 2
    nx0 = int(round(cx - nw / 2)); nx0 = min(max(nx0, B + 1), W - B - 1 - nw); nx1 = nx0 + nw - 1
    cy = (y0 + y1 + 1) / 2
    ny0 = int(round(cy - nh / 2)); ny0 = min(max(ny0, B), H - B - nh); ny1 = ny0 + nh - 1
    # build the new box from the old one: corners kept, edges stretched
    old = a[oy0:oy1 + 1, ox0:ox1 + 1]
    ow, oh = old.shape[1], old.shape[0]; NW, NH = nw + 2 * B, nh + 2 * B
    c = B + 2
    xs = np.r_[np.arange(c), np.full(max(0, NW - 2 * c), ow // 2), np.arange(ow - c, ow)][:NW]
    ys = np.r_[np.arange(c), np.full(max(0, NH - 2 * c), oh // 2), np.arange(oh - c, oh)][:NH]
    # middle row/col of the old box may contain text: take a clean column (navy) for the stretch
    box = old[ys][:, xs].copy()
    inner = np.zeros((NH, NW), bool); inner[B:NH - B, B:NW - B] = True
    box[inner] = NAVY                                              # flat navy field (as in the originals)
    # keep the original 1px dark shading just inside the border
    shade_top = old[B, ow // 2] if np.abs(old[B, ow // 2] - NAVY).max() > 8 else None
    region_old = (slice(oy0, oy1 + 1), slice(ox0, ox1 + 1))
    new = a.copy()
    new[region_old] = 0                                            # background behind the old box was black
    new[ny0 - B:ny1 + B + 1, nx0 - B:nx1 + B + 1] = box
    # render text
    big = Image.new('L', (int(round(W * S / XS)), H * S), 0); dr = ImageDraw.Draw(big)
    ty = ny0 + PADT
    for k, ln in enumerate(lines):
        lw = f.getlength(ln) * XS / S
        tx = (nx0 + nx1 + 1) / 2 - lw / 2
        asc, desc = f.getmetrics()
        yy = ty + k * lh + (lh - (asc + desc) / S) / 2
        dr.text((tx / XS * S, yy * S), ln, font=f, fill=255)
    if note:
        lw = fn.getlength(note) * XS / S; tx = (nx0 + nx1 + 1) / 2 - lw / 2
        asc, desc = fn.getmetrics(); yy = ty + len(lines) * lh + (NOTEPITCH - (asc + desc) / S) / 2
        dr.text((tx / XS * S, yy * S), note, font=fn, fill=255)
    al = np.array(big.resize((W, H), Image.BOX)).astype(np.float32)[..., None] / 255.0
    out = new.astype(np.float32)
    if SHADOW:
        sh = np.zeros_like(al); sh[1:, 1:] = al[:-1, :-1]
        out = out * (1 - sh) + np.array([0, 0, 16]) * sh
    out = out * (1 - al) + INK * al
    # back to the existing palette
    ch = np.abs(out - a).sum(2) > 2
    cand = np.where(pal != 0)[0]
    dd = ((out[ch][:, None, :] - P[cand][None]) ** 2).sum(2)
    nidx = idx.copy(); nidx[ch] = cand[dd.argmin(1)]
    if (pal == 0).any():                                         # keep pure black where we cleared to black
        z = int(np.where(pal == 0)[0][0])
        blk = ch & (np.abs(out).sum(2) < 4); nidx[blk] = z
    t = bytearray(t); t[po:po + W * H] = nidx.tobytes()
    Image.fromarray(np.concatenate([a, P[nidx]], 1).astype(np.uint8)).resize((W * 4, H * 2), Image.NEAREST).save(
        os.path.join(prev, f'{name}.png'))
    return bytes(t), (round(float(size), 2), len(lines), nw - inner_w)

k = 0; total = 0
for o, ents in containers():
    streams = []; changed = False
    for (st, sz) in ents:
        h, _ = npk.lz_stream_decode(bytes(d), o + st, out_len=2048)
        L = tim_len(h); t, _ = npk.lz_stream_decode(bytes(d), o + st, out_len=L)
        if k in caps:
            t, info2 = process(t, caps[k], f'{k:03d}'); changed = True
            print(k, repr(caps[k]), info2)
        streams.append(t); k += 1
    if not changed: continue
    # space available: up to the next used sector
    end0 = max(st + sz for st, sz in ents); lim = o + ((end0 + 2047) // 2048) * 2048
    while lim < len(d) and lim // 2048 not in covered and d[lim:lim + 2048] == b'\0' * 2048: lim += 2048
    enc = [npk.encode_stream(s) for s in streams]
    for e, s in zip(enc, streams): assert npk.lz_stream_decode(e, 0, out_len=len(s))[0] == s
    hs = 8 * len(enc); hdr = b''; pos = hs
    for e in enc: hdr += struct.pack('<2I', pos, len(e)); pos += len(e)
    blob = hdr + b''.join(enc)
    assert o + len(blob) <= lim, f'container @{o:#x} grew past {lim:#x} ({len(blob)} > {lim - o})'
    d[o:lim] = blob + b'\0' * (lim - o - len(blob)); total += 1
open(dst, 'wb').write(d)
print('containers rewritten', total, '->', dst)
