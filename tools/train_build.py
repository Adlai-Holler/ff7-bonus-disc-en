"""Repaint the Shinra Railway info page (FF_TTOWN.NPK scene 8, 8bpp TIM) in English.
usage: train_build.py <in FF_TTOWN.NPK> <out FF_TTOWN.NPK> <preview.png>"""
import sys, os, struct, pickle
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '/home/claude/scripts')
import npk

src, dst, prev = sys.argv[1:4]
d = bytearray(open(src, 'rb').read())
info = pickle.load(open('/home/claude/npk/town/tt_info.pkl', 'rb'))
K = 8; _, off, nblk, W0, H0, _ = info[K]
t = bytearray(npk.game_decode(bytes(d), off))
cl = struct.unpack_from('<I', t, 8)[0]
pal = np.frombuffer(bytes(t), '<u2', count=256, offset=20)
P = np.stack([(pal & 31) << 3, ((pal >> 5) & 31) << 3, ((pal >> 10) & 31) << 3], -1).astype(int)
po = 8 + cl; w2, H = struct.unpack_from('<HH', t, po + 8); W = w2 * 2; po += 12
idx = np.frombuffer(bytes(t), np.uint8, count=W * H, offset=po).reshape(H, W).copy()
a = P[idx].astype(np.float32)

TOP = int(os.environ.get('TTOP', '96'))          # everything below this row is the Japanese text block on black
XS = float(os.environ.get('TXS', '1.3')); S = 4
SERIF = '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'
ITAL = '/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf'
INK = np.array([228, 228, 228])

TITLE = 'Shinra Railway  Muka 100 Type 90  Model 600'
BODY = ("A railway linking Midgar's Sector 0 (the central district where the Shinra Building towers) "
        "with Sectors 1-8 (the plates that make up Midgar). The Muka 100 Type 90 is currently the "
        "mainstay of the line. It is also heavily relied on as the only way to travel between the "
        "plate and the slums below.")

black = int(np.argmin(P.sum(1)))
blank = a.copy(); blank[TOP:] = P[black]

def wrap(text, f, maxw):
    lines, cur = [], ''
    for w in text.split(' '):
        tryl = (cur + ' ' + w).strip()
        if f.getlength(tryl) * XS / S <= maxw: cur = tryl
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

big = Image.new('L', (int(W * S / XS), H * S), 0); dr = ImageDraw.Draw(big)
ft = ImageFont.truetype(SERIF, int(18 * S)); fb = ImageFont.truetype(ITAL, int(12.5 * S))
X0, X1 = 62, 488
ft = ImageFont.truetype(SERIF, int(16 * S)); fs = ImageFont.truetype(SERIF, int(11.5 * S))
main, small = 'Shinra Railway   Muka 100 Type 90 ', 'Model 600'
dr.text((76 / XS * S, 106 * S), main, font=ft, fill=255)
dr.text((76 / XS * S + ft.getlength(main), 110.5 * S), small, font=fs, fill=255)
print('title ends at x', 76 + (ft.getlength(main) + fs.getlength(small)) * XS / S)
lines = wrap(BODY, fb, X1 - X0)
for k, ln in enumerate(lines):
    dr.text((X0 / XS * S, (136 + k * 15.5) * S), ln, font=fb, fill=255)
al = np.array(big.resize((W, H), Image.BOX)).astype(np.float32)[..., None] / 255.0
out = blank * (1 - al) + INK * al
ch = np.abs(out - a).sum(2) > 2
dd = ((out[ch][:, None, :] - P[None]) ** 2).sum(2)
nidx = idx.copy(); nidx[ch] = dd.argmin(1)
t[po:po + W * H] = nidx.tobytes()
enc = npk.encode_blocks(bytes(t), nblk)
assert npk.game_decode(enc + b'\0' * 2048, 0) == bytes(t)
slot = ((nblk * 1024 + 2047) // 2048) * 2048
assert len(enc) <= slot, (len(enc), slot)
d[off:off + slot] = enc + b'\0' * (slot - len(enc))
open(dst, 'wb').write(d)
Image.fromarray(np.concatenate([a, P[nidx]], 0).astype(np.uint8)).resize((W * 2, H * 4), Image.NEAREST).save(prev)
print('lines', len(lines), 'last y', 136 + (len(lines) - 1) * 15.5, 'blocks', len(enc) // 1024, '/', nblk)
