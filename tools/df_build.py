"""Translate the DATA FILE menu images in NPK_DF.NPK and repack.
usage: df_build.py <orig NPK_DF> <out NPK_DF> <preview_dir>"""
import sys, os, struct
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '/home/claude/scripts')
import npk, tim

src, dst, prev = sys.argv[1:4]
d = open(src, 'rb').read()
hs = struct.unpack_from('<I', d, 0)[0]
tab = struct.unpack_from(f'<{hs // 4}I', d, 0)          # (16, size0, start1, size1)
LIMIT = 106496                                          # next data in the file starts here

def tim_size(t):
    clen = struct.unpack_from('<I', t, 8)[0]
    return 8 + clen + struct.unpack_from('<I', t, 8 + clen)[0]

streams = []; o = hs
for k in range(2):
    hdr, _ = npk.lz_stream_decode(d, o, out_len=4096)
    t, o2 = npk.lz_stream_decode(d, o, out_len=tim_size(hdr))
    streams.append(bytearray(t)); o = o2
assert o == tab[2] + tab[3], (o, tab)

LABELS = ['Items', 'Characters', 'Vehicles', 'Artwork']
HX = float(os.environ.get('HX', '1.6'))
FONT = os.environ.get('DFFONT', '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf')
SIZE = float(os.environ.get('DFSIZE', '16'))
S = 4

rng = np.random.default_rng(7)
def fit_plate(img, y0, y1, x0, x1):
    """Rebuild plate rows y0..y1 (incl), cols x0..x1 (incl) as a smooth per-row quadratic in x, ignoring text/shadow."""
    a = img.astype(np.float32); out = a.copy()
    xs = np.arange(x0, x1 + 1)
    textmask = np.zeros((y1 - y0 + 1, x1 - x0 + 1), bool)
    for y in range(y0, y1 + 1):
        row = a[y, x0:x1 + 1]
        bad = row.min(1) > 170                           # white glyphs
        bad = cv2.dilate(bad.astype(np.uint8)[None], np.ones((1, 5), np.uint8))[0].astype(bool)
        for it in range(4):
            good = ~bad
            coef = [np.polyfit(xs[good], row[good, c], 2) for c in range(3)]
            fit = np.stack([np.polyval(cf, xs) for cf in coef], 1)
            dev = np.abs(row - fit).sum(1)
            bad = dev > 45
            bad = cv2.dilate(bad.astype(np.uint8)[None], np.ones((1, 3), np.uint8))[0].astype(bool)
        textmask[y - y0] = bad
        # give rebuilt pixels the plate's own grain: residual of a random untouched pixel in this row
        good = np.where(~bad)[0]
        res = row - fit
        pick = rng.choice(good, size=bad.sum()) if len(good) else None
        fill = fit.copy()
        if pick is not None: fill[bad] = fit[bad] + res[pick]
        out[y, x0:x1 + 1] = np.where(bad[:, None], fill, row)
    return out.clip(0, 255).astype(np.uint8), textmask

def draw_label(img, y0, y1, x0, x1, label, shadow):
    """Draw centred white label with a vertical fade and a drop shadow onto plate rows y0..y1."""
    H, W = img.shape[:2]
    big = Image.fromarray(img).resize((W * S, H * S), Image.NEAREST)
    f = ImageFont.truetype(FONT, int(SIZE * S))
    TRACK = float(os.environ.get('TRACK', '0.8')) * S        # extra space between letters (image px, before stretch)
    tw = f.getlength(label) + TRACK * (len(label) - 1); bb = f.getbbox(label)
    tmp = Image.new('L', (int(tw) + 8 * S, int(SIZE * S * 1.6)), 0)
    dr = ImageDraw.Draw(tmp); x = 0.0
    for ch in label:
        dr.text((x, 0), ch, font=f, fill=255); x += f.getlength(ch) + TRACK
    tmp = tmp.resize((int(tmp.width * HX), tmp.height), Image.LANCZOS)
    w = tw * HX / S; ch = (bb[3] - bb[1]) / S
    cx = (x0 + x1 + 1) / 2; cy = (y0 + y1 + 1) / 2
    px = cx - w / 2; py = cy - ch / 2 - bb[1] / S
    arr = np.array(big).astype(np.float32)
    def comp(mask_img, dx, dy, color_fn):
        m = Image.new('L', big.size, 0); m.paste(mask_img, (int((px + dx) * S), int((py + dy) * S)))
        al = np.array(m).astype(np.float32)[..., None] / 255.0
        return al, color_fn
    # shadow: same glyph, offset like the original (4 px right, 2 px down in image pixels), softened,
    # darkening whatever is underneath (the original shadow is ~0.75x the plate colour)
    SDX = float(os.environ.get('SDX', '4')); SDY = float(os.environ.get('SDY', '2'))
    SDARK = float(os.environ.get('SDARK', '0.72')); SBLUR = float(os.environ.get('SBLUR', '0.8'))
    al, _ = comp(tmp, SDX, SDY, None)
    al = cv2.GaussianBlur(al[..., 0], (0, 0), SBLUR * S)[..., None]
    arr = arr * (1 - al * (1 - SDARK))
    # fill: vertical fade white -> light grey
    al, _ = comp(tmp, 0, 0, None)
    ys = (np.arange(H * S)[:, None] / S - (cy - ch / 2)) / max(ch, 1)
    fade = np.clip(ys, 0, 1)
    top = np.array([255, 255, 255], np.float32); bot = np.array([255, 255, 255], np.float32)
    col = top * (1 - fade[..., None]) + bot * fade[..., None]
    arr = arr * (1 - al) + col * al
    small = Image.fromarray(arr.clip(0, 255).astype(np.uint8)).resize((W, H), Image.BOX)
    return np.array(small)

def plate_shadow(orig, fixed, tmask_box):
    """Typical drop-shadow colour: original pixels much darker than the rebuilt plate inside the text mask."""
    o = orig.astype(int); f = fixed.astype(int)
    dark = (f.sum(2) - o.sum(2) > 90) & tmask_box
    return tuple(int(v) for v in np.median(o[dark], 0)) if dark.any() else (40, 0, 10)

PLATES = {
    0: [(125, 141, 140, 371), (151, 166, 140, 371), (177, 192, 140, 371), (202, 217, 140, 371)],
    1: [(2, 19, 5, 245), (26, 42, 5, 245), (50, 66, 5, 245), (74, 90, 5, 245)],
}
for k in (0, 1):
    t = streams[k]; pal, idx, pixoff = tim.parse(bytes(t)); im = tim.rgb(pal, idx)
    work = im.copy()
    for (y0, y1, x0, x1), label in zip(PLATES[k], LABELS):
        fixed, tm = fit_plate(work, y0, y1, x0, x1)
        box = np.zeros(im.shape[:2], bool); box[y0:y1 + 1, x0:x1 + 1] = tm
        sh = plate_shadow(im, fixed, box)
        work = fixed
        work = draw_label(work, y0, y1, x0, x1, label, sh)
    Image.fromarray(work).save(os.path.join(prev, f'df{k}_en.png'))
    # quantize changed pixels to this image's palette
    P = tim.pal_rgb(pal); nidx = idx.copy()
    ch = np.abs(work.astype(int) - im.astype(int)).sum(2) > 0
    cand = np.arange(len(P)); cand = cand[pal[cand] != 0]
    dd = ((work[ch].astype(int)[:, None, :] - P[cand][None]) ** 2).sum(2)
    nidx[ch] = cand[dd.argmin(1)]
    t[pixoff:pixoff + nidx.size] = nidx.tobytes()
    Image.fromarray(tim.rgb(pal, nidx)).save(os.path.join(prev, f'df{k}_en_q.png'))

e0 = npk.encode_stream(bytes(streams[0])); e1 = npk.encode_stream(bytes(streams[1]))
assert npk.lz_stream_decode(e0, 0, out_len=len(streams[0]))[0] == bytes(streams[0])
assert npk.lz_stream_decode(e1, 0, out_len=len(streams[1]))[0] == bytes(streams[1])
total = hs + len(e0) + len(e1)
print('stream sizes', len(e0), len(e1), 'end', total, 'limit', LIMIT, '(orig end', tab[2] + tab[3], ')')
assert total <= LIMIT
out = bytearray(d)
out[0:hs] = struct.pack('<4I', hs, len(e0), hs + len(e0), len(e1))
out[hs:LIMIT] = e0 + e1 + b'\0' * (LIMIT - total)
open(dst, 'wb').write(out)
print('wrote', dst)
