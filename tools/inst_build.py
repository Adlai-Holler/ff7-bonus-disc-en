"""Translate S1G/INST_M.S1G (mouse) and S1G/INST_P.S1G (controller) instruction screens.
These are raw 8bpp TIMs (no compression): pixels are rewritten in place, palette untouched.
usage: inst_build.py <base_dir> <out_dir> <preview_dir>"""
import sys, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '/home/claude/scripts')
import tim

base, outd, prev = sys.argv[1:4]
HX = float(os.environ.get('HX', '1.6'))
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
S = 4
rng = np.random.default_rng(3)

def render_mask(W, H, items):
    """items: list of (x, y, text, size). x,y = top-left in image px. Returns float alpha HxW and widths."""
    big = Image.new('L', (W * S, H * S), 0)
    widths = []
    for x, y, txt, size in items:
        f = ImageFont.truetype(FONT, int(size * S))
        w = f.getlength(txt)
        tmp = Image.new('L', (int(w) + 6 * S, int(size * S * 1.6)), 0)
        ImageDraw.Draw(tmp).text((0, 0), txt, font=f, fill=255)
        tmp = tmp.resize((max(1, int(tmp.width * HX)), tmp.height), Image.LANCZOS)
        big.paste(tmp, (int(x * S), int(y * S)), tmp)
        widths.append(w * HX / S)
    return np.array(big.resize((W, H), Image.BOX)).astype(np.float32) / 255.0, widths

def text_w(txt, size):
    return ImageFont.truetype(FONT, int(size * S)).getlength(txt) * HX / S

def ink_top(txt, size):
    f = ImageFont.truetype(FONT, int(size * S)); bb = f.getbbox(txt)
    return bb[1] / S, (bb[3] - bb[1]) / S

def fit_rows(a, y0, y1, x0, x1, bad_fn):
    """Rebuild rows y0..y1 between x0..x1: pixels flagged by bad_fn are replaced by a per-row quadratic fit + grain."""
    out = a.copy(); xs = np.arange(x0, x1 + 1)
    for y in range(y0, y1 + 1):
        row = a[y, x0:x1 + 1].astype(float)
        bad = bad_fn(row)
        bad = cv2.dilate(bad.astype(np.uint8)[None], np.ones((1, 3), np.uint8))[0].astype(bool)
        good = ~bad
        if good.sum() < 6: continue
        coef = [np.polyfit(xs[good], row[good, c], 2) for c in range(3)]
        fit = np.stack([np.polyval(cf, xs) for cf in coef], 1)
        res = row - fit; pick = rng.choice(np.where(good)[0], size=bad.sum())
        fill = fit.copy(); fill[bad] = fit[bad] + res[pick]
        out[y, x0:x1 + 1] = np.where(bad[:, None], fill, row)
    return out

def pill_interior(a, box):
    """box = x,y,w,h of the pill fill blob; return interior rows/cols (inside the rim, between the end caps)."""
    x, y, w, h = box
    return y + 2, y + h - 3, x + h // 2, x + w - h // 2

def do_pill(a, alpha_items, box, label, color, keep_left=0, size=11.0):
    y0, y1, x0, x1 = pill_interior(a, box)
    ex0 = x0 + keep_left
    med = np.median(a[y0:y1 + 1, ex0:x1 + 1].reshape(-1, 3), 0).sum()
    a = fit_rows(a, y0, y1, ex0, x1, lambda r: r.sum(1) > med + 60)
    avail = (x1 - ex0) + (box[3] // 2 - 9 if keep_left else box[3] // 3)
    while text_w(label, size) > avail and size > 6: size -= 0.25
    tw = text_w(label, size); top, ih = ink_top(label, size)
    if keep_left:
        tx = ex0 + 3
    else:
        tx = box[0] + (box[2] - tw) / 2
    ty = box[1] + (box[3] - ih) / 2 - top
    alpha_items.append(((tx, ty, label, size), color))
    return a

def bg_fill(a, region, empty_rows):
    """Replace text pixels in region (y0,y1,x0,x1) with background noise sampled from empty rows."""
    y0, y1, x0, x1 = region
    pool = a[empty_rows[0]:empty_rows[1], 4:508].reshape(-1, 3)
    pool = pool[pool.max(1) < 60]
    sub = a[y0:y1 + 1, x0:x1 + 1]
    txt = sub.max(2) > 60
    txt = cv2.dilate(txt.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    sub[txt] = pool[rng.integers(0, len(pool), txt.sum())]
    a[y0:y1 + 1, x0:x1 + 1] = sub
    return a

def leader_line(items, y, left, right, size, xl, xr, color):
    """left label at xl, dot leader, right label at xr."""
    items.append(((xl, y, left, size), color))
    lw = text_w(left, size); dot = text_w('.', size)
    d0 = xl + lw + 3; d1 = xr - 4
    n = int((d1 - d0) / (dot * 1.15))
    if n > 0:
        items.append(((d0, y, '.' * n, size), color))
    items.append(((xr, y, right, size), color))

def composite(a, items, H, W):
    out = a.astype(np.float32)
    for (x, y, txt, size), col in items:
        al, _ = render_mask(W, H, [(x, y, txt, size)])
        if callable(col):
            c = col(H, W)
        else:
            c = np.broadcast_to(np.array(col, np.float32), (H, W, 3))
        out = out * (1 - al[..., None]) + c * al[..., None]
    return out.clip(0, 255).astype(np.uint8)

def vgrad(top, bot, y0, y1):
    def f(H, W):
        t = np.clip((np.arange(H)[:, None] - y0) / max(1, (y1 - y0)), 0, 1)[..., None]
        return np.broadcast_to(np.array(top, np.float32) * (1 - t) + np.array(bot, np.float32) * t, (H, W, 3))
    return f

def save(name, t, pal, idx, pixoff, new, im):
    P = tim.pal_rgb(pal); cand = np.where(pal != 0)[0]
    ch = np.abs(new.astype(int) - im.astype(int)).sum(2) > 0
    dd = ((new[ch].astype(int)[:, None, :] - P[cand][None]) ** 2).sum(2)
    nidx = idx.copy(); nidx[ch] = cand[dd.argmin(1)]
    t = bytearray(t); t[pixoff:pixoff + nidx.size] = nidx.tobytes()
    open(os.path.join(outd, name + '.S1G'), 'wb').write(t)
    Image.fromarray(tim.rgb(pal, nidx)).save(os.path.join(prev, name + '_en.png'))
    print(name, 'pixels changed', int(ch.sum()))

PILL_TXT = (216, 216, 224)
CYAN = vgrad((0, 160, 160), (0, 112, 120), 0, 0)   # replaced per line below
def cyan(y, h): return vgrad((0, 168, 168), (0, 104, 112), y, y + h)
def orange(y, h): return vgrad((248, 168, 16), (168, 88, 0), y, y + h)

# ---------------- mouse page
t = open(os.path.join(base, 'S1G/INST_M.S1G'), 'rb').read()
pal, idx, pixoff = tim.parse(t); im = tim.rgb(pal, idx); a = im.astype(int); H, W = a.shape[:2]
items = []
for box, lab in (((109, 27, 86, 19), 'Left button'), ((305, 27, 88, 19), 'Right button')):
    a = do_pill(a, items, box, lab, PILL_TXT)
a = bg_fill(a, (164, 213, 40, 500), (216, 238))
SZ = 10.5; XL, XR = 53, 271
for i, (l, r) in enumerate((('Left button', 'Confirm'), ('Right button', 'Cancel'), ('Move mouse', 'Move cursor'))):
    y = (167, 183, 200)[i]; top, ih = ink_top('Mg', SZ); yy = y - top
    leader_line(items, yy, l, r, SZ, XL, XR, cyan(y, 11))
new = composite(a, items, H, W)
save('INST_M', t, pal, idx, pixoff, new, im)

# ---------------- controller page
t = open(os.path.join(base, 'S1G/INST_P.S1G'), 'rb').read()
pal, idx, pixoff = tim.parse(t); im = tim.rgb(pal, idx); a = im.astype(int); H, W = a.shape[:2]
items = []
GREY = [((107, 10, 102, 20), 'L2 button'), ((298, 10, 102, 20), 'R2 button'),
        ((66, 31, 103, 20), 'L1 button'), ((338, 31, 103, 20), 'R1 button'),
        ((51, 73, 88, 20), 'D-pad'),
        ((81, 134, 138, 20), 'SELECT button'), ((284, 134, 139, 20), 'START button')]
for box, lab in GREY:
    a = do_pill(a, items, box, lab, PILL_TXT)
# coloured pills: find them (saturated blobs on the right), keep the symbol, replace the katakana
# coloured pills (measured): keep the symbol at the left, replace the katakana with "button"
cp = [(367, 52, 89, 20), (367, 73, 89, 20), (368, 94, 89, 19), (368, 114, 89, 20)]
for box in cp:
    x, y, w, h = box
    flat = a[y + 3:y + h - 3, x + 30:x + w - 8].reshape(-1, 3)
    tc = tuple(int(v) for v in flat[flat.sum(1) >= np.percentile(flat.sum(1), 95)].mean(0))
    a = do_pill(a, items, box, 'button', tc, keep_left=int(os.environ.get('KEEPL', '15')))
a = bg_fill(a, (155, 231, 20, 500), (232, 240))
SZ = 10.0; XL, XR = 73, 271
SZ = 9.5
for i, (l, r) in enumerate((('○ button', 'Confirm'), ('× button', 'Cancel'),
                            ('L1 / R1 buttons', 'Switch screens'), ('D-pad', 'Move cursor'),
                            ('SELECT button', 'Sparkles (field screens)'))):
    y = (155, 166, 177, 188, 199)[i]; top, ih = ink_top('Mg', SZ)
    leader_line(items, y - top, l, r, SZ, XL, XR, cyan(y, 10))
FS = 9.5
for i, ln in enumerate(('Press ○ on the controller or the left mouse button',
                        'to see the mouse instructions.')):
    y = (211, 221)[i]; top, ih = ink_top('Mg', FS)
    items.append(((36, y - top, ln, FS), orange(y, 9)))
new = composite(a, items, H, W)
save('INST_P', t, pal, idx, pixoff, new, im)
