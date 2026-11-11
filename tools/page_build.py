"""Prototype: translate page 0 of NPK_WEP (Buster Sword) and repack NPK_WEP.
usage: page_build.py <orig NPK_WEP> <out NPK_WEP> <preview.png>"""
import sys, struct, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '/home/claude/scripts')
import npk, tim

src, dst, prev = sys.argv[1:4]
d = bytearray(open(src, 'rb').read())
its = npk.items(d)
off, nblk = its[0]
slot_end = its[1][0]
t = bytearray(npk.game_decode(bytes(d), off))
pal, idx, pixoff = tim.parse(bytes(t))
im = tim.rgb(pal, idx)

# --- erase Japanese text
a = im.astype(int); L = a.sum(2)
red = (a[..., 0] - a[..., 1] > 55) & (a[..., 1] < 110)
ink = (L < 420) | red
mask = np.zeros(L.shape, np.uint8)
mask[27:167, 265:448] = ink[27:167, 265:448]
mask[25:48, 42:205] = ink[25:48, 42:205]
mask = cv2.dilate(mask, np.ones((3, 3), np.uint8))
mask[48:50, 40:206] = 0            # keep title underline
clean = cv2.inpaint(np.ascontiguousarray(im), mask * 255, 5, cv2.INPAINT_TELEA)
# optional hand-retouched blank parchment: used wherever this page had text
import os
TPL = os.environ.get('TPL')
UL = None
if TPL and os.path.exists(TPL):
    tpl = np.array(Image.open(TPL).convert('RGB'))
    # stats page never has art: take the whole text block from the template
    # use the (tone-matched) template only where this page had text, with a wide margin for the
    # faint glyph edges; feather the boundary so it blends into the original's own pixels
    ink_all = ((L < 420) | red).astype(np.uint8)
    boxes = np.zeros(L.shape, np.uint8)
    boxes[25:170, 262:470] = 1                     # stats block
    boxes[20:51, 38:232] = 1                       # title block
    D = int(os.environ.get("DIL", "9")); rep = cv2.dilate(ink_all * boxes, np.ones((D, D), np.uint8)) & cv2.dilate(boxes, np.ones((D, D), np.uint8))
    diff = np.abs(im.astype(int) - tpl.astype(int)).sum(2)
    art = (diff > 120) & (ink_all == 0)            # item picture pixels near the title: keep them
    rep[art & (boxes > 0)] = 0
    a = cv2.GaussianBlur(rep.astype(np.float32), (0, 0), 1.2)
    a = np.maximum(a, rep * 0.0)[..., None]
    a[cv2.erode(rep, np.ones((3, 3), np.uint8)).astype(bool)] = 1.0
    clean = (clean.astype(np.float32) * (1 - a) + tpl.astype(np.float32) * a).astype(np.uint8)
    # remember underline darkening ratio from the original page (row 49)
    ratio = np.median(im[49, 70:200].astype(float) / np.maximum(im[46, 70:200].astype(float), 1), 0)
    UL = (49, 44, ratio)
blank = clean.copy()
# --- draw English (4x supersampled)
S = 4
big = Image.fromarray(clean).resize((512 * S, 240 * S), Image.NEAREST)
F = '/usr/share/fonts/truetype/liberation/LiberationSerif-'
RED = (96, 0, 16); BLK = (0, 0, 0)
layers = []
HX = float(__import__('os').environ.get('HX', '1.35'))   # horizontal stretch (512-wide mode shown at 4:3)
def text(x, y, s, size, color, bold=False):
    f = ImageFont.truetype(F + ('Bold' if bold else 'Regular') + '.ttf', int(size * S))
    tmp = Image.new('L', (int(f.getlength(s)) + 8 * S, int(size * S * 1.6)), 0)
    ImageDraw.Draw(tmp).text((0, 0), s, font=f, fill=255)
    tmp = tmp.resize((int(tmp.width * HX), tmp.height), Image.LANCZOS)
    m = Image.new('L', big.size, 0); m.paste(tmp, (int(x * S), int(y * S)))
    layers.append((m, color)); return f.getlength(s) * HX / S
tw = text(48, 25.5, 'Buster Sword', 19, BLK)
rows = [('Equip', 'Cloud'), ('Attack', '18'), ('Bonus', 'Magic +2'), ('Hit %', '96'),
        ('Slots', None), ('Growth', 'Normal'), ('Sell', 'No'), ('Price', 'Not sold'),
        (None, "Can't be thrown"), ('Element', 'Cut'), ('How to get', ''),
        (None, "● Cloud's starting gear")]
y0, pitch, sz = 28.6, 11.25, 12.2
for i, (lab, val) in enumerate(rows):
    y = y0 + i * pitch; x = 271
    if lab:
        x += text(x, y, lab, sz, RED, True) + 5
    if val:
        text(x, y, val, sz, BLK)
    if lab == 'Slots':
        m = Image.new('L', big.size, 0); dr = ImageDraw.Draw(m); cx = x + 4 * HX
        for k in range(2):
            c = cx + k * 14 * HX
            dr.ellipse(((c - 3.6 * HX) * S, (y + 2.6) * S, (c + 3.6 * HX) * S, (y + 9.8) * S), outline=255, width=3)
        dr.line(((cx + 4.5 * HX) * S, (y + 6.2) * S, (cx + 9.5 * HX) * S, (y + 6.2) * S), fill=255, width=3)
        layers.append((m, BLK))
out = np.array(big).astype(float)
for m, c in layers:
    al = np.array(m)[..., None] / 255.0
    out = out * (1 - al) + np.array(c) * al
new = np.array(Image.fromarray(out.clip(0, 255).astype(np.uint8)).resize((512, 240), Image.BOX))
if UL:
    uy, ux0, ratio = UL
    ux1 = int(48 + tw + 8)
    new = new.astype(float); new[uy, ux0:ux1] *= ratio; new = new.clip(0, 255).astype(np.uint8)

# --- quantize only changed pixels to palette (index 0 excluded if transparent)
P = tim.pal_rgb(pal)
changed = np.abs(new.astype(int) - im.astype(int)).sum(2) > 0
nidx = idx.copy()
cand = np.arange(len(P)); cand = cand[pal[cand] != 0]
flat = new[changed].astype(int)
dd = ((flat[:, None, :] - P[cand][None]) ** 2).sum(2)
nidx[changed] = cand[dd.argmin(1)]
# keep the original palette index wherever the new pixel is visually indistinguishable from it
# (preserves the original's highly compressible paper grain; text areas still get new pixels)
KEEP = int(os.environ.get('KEEP', '24'))
same = changed & (np.abs(new.astype(int) - P[idx]).sum(2) <= KEEP)
nidx[same] = idx[same]
t[pixoff:pixoff + nidx.size] = nidx.tobytes()
Image.fromarray(tim.rgb(pal, nidx)).resize((1024, 480), Image.NEAREST).save(prev)
Image.fromarray(blank).save(prev.replace('.png', '_blank.png'))

# --- recompress and repack in place
enc = npk.encode_blocks(bytes(t), nblk)
assert npk.game_decode(enc + b'\0' * 2048, 0) == bytes(t), 'round trip failed'
room = slot_end - off
print('encoded', len(enc), 'room', room, 'blocks', len(enc) // 1024)
assert len(enc) <= room
d[off:slot_end] = enc + b'\0' * (room - len(enc))
open(dst, 'wb').write(d)
print('wrote', dst)
