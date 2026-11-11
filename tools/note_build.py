"""Translate the two Shinra Mansion notes stored in TOWN/FF_TTOWN.NPK and repack the container in place.
usage: note_build.py <orig FF_TTOWN.NPK> <out FF_TTOWN.NPK> <preview_dir>"""
import sys, os, struct, textwrap
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '/home/claude/scripts')
import npk, tim

src, dst, prev = sys.argv[1:4]
d = bytearray(open(src, 'rb').read())
C = 33468416            # sector-aligned container: [16, size0, start1, size1] + two LZ streams
LIMIT = 33488896        # next scene chain starts here
hs, s0, st1, s1 = struct.unpack_from('<4I', d, C)
assert (hs, s0, st1, s1) == (16, 9504, 9520, 9742), (hs, s0, st1, s1)
assert not any(d[C + st1 + s1:LIMIT]), 'slack after container is not empty'

def dec(o):
    h, _ = npk.lz_stream_decode(bytes(d), o, out_len=4096)
    clen = struct.unpack_from('<I', h, 8)[0]
    n = 8 + clen + struct.unpack_from('<I', h, 8 + clen)[0]
    return bytearray(npk.lz_stream_decode(bytes(d), o, out_len=n)[0])

NOTES = [
    ("All who obstruct my research must be removed. That man from the Turks is no exception. "
     "I modified the Turk biologically and left him sleeping in the basement. "
     "Look for him if you are curious. But... this is only a game I thought up on a whim. "
     "You need not play along."),
    ("Turn the safe's dial carefully but fast: within 20 seconds. Don't overshoot!\n"
     "Hints for the 4 dials...\n"
     "Dial [1]: lid of the box with the most oxygen\n"
     "Dial [2]: back of the black & white with no sky\n"
     "Dial [3]: creaky floor by the 2F chair...\n"
     "From there: 5 left, 9 up, 2 left, 6 up."),
]
HX = float(os.environ.get('HX', '1.6'))
FONT = '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'
INK = (22, 22, 22)
S = 4

def process(t, text, name):
    pal, idx, pixoff = tim.parse(bytes(t))
    im = tim.rgb(pal, idx); a = im.astype(int); L = a.sum(2); H, W = L.shape
    ys, xs = np.where(L > 300)
    py0, py1, px0, px1 = ys.min(), ys.max(), xs.min(), xs.max()
    # text box: inside the paper, away from the edges; the curled corner (bottom-right) is left alone
    ty0, ty1, tx0, tx1 = py0 + 3, py1 - 3, px0 + 3, px1 - 2
    curl = np.zeros(L.shape, bool)
    for y in range(H):
        for x in range(W):
            if (x - (px1 - 34)) + (y - (py1 - 30)) > 30: curl[y, x] = True
    box = np.zeros(L.shape, bool); box[py0 + 1:ty1 + 1, tx0:tx1 + 1] = True; box &= ~curl
    # per-column paper level from the brightest half of each column inside the box (text is dark)
    colbg = np.zeros((W, 3))
    for x in range(tx0, tx1 + 1):
        col = a[py0 + 1:ty1 + 1, x][box[py0 + 1:ty1 + 1, x]]
        if len(col):
            k = col.sum(1); keep = col[k >= np.percentile(k, 50)]
            colbg[x] = np.median(keep, 0)
    bgL = colbg.sum(1)
    text = box & (L < bgL[None, :] - 60)
    text = cv2.dilate(text.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & box
    clean = a.copy()
    clean[text] = colbg[np.where(text)[1]]
    # lay out English: shrink until it fits the box
    for size in np.arange(14.0, 7.0, -0.25):
        f = ImageFont.truetype(FONT, int(size * S))
        wpx = (tx1 - tx0 - 2) * S / HX
        wlast = (tx1 - tx0 - 30) * S / HX
        lines = []
        for para in TEXT_OF[name].split('\n'):
            words = para.split(' '); cur = ''
            for wd in words:
                trial = (cur + ' ' + wd).strip()
                if f.getlength(trial) <= wpx: cur = trial
                else: lines.append(cur); cur = wd
            lines.append(cur)
        pitch = size * float(os.environ.get('PITCH', '1.0'))
        nfit = len(lines) * pitch <= (ty1 - ty0 - 1)
        safe = all(f.getlength(l) <= (wlast if (ty0 + 1 + (k + 1) * pitch) > ty1 - 26 else wpx) for k, l in enumerate(lines))
        if nfit and safe: break
    pitch = min(size * 1.22, (ty1 - ty0 - 2) / len(lines))   # spread lines to fill the paper
    big = Image.fromarray(clean.clip(0, 255).astype(np.uint8)).resize((W * S, H * S), Image.NEAREST)
    mask = Image.new('L', big.size, 0); dr = ImageDraw.Draw(mask)
    y = ty0 + 1
    for ln in lines:
        tmp = Image.new('L', (int(f.getlength(ln)) + 4 * S, int(size * S * 1.5)), 0)
        ImageDraw.Draw(tmp).text((0, 0), ln, font=f, fill=255)
        tmp = tmp.resize((int(tmp.width * HX), tmp.height), Image.LANCZOS)
        mask.paste(tmp, (int((tx0 + 1) * S), int(y * S)), tmp)
        y += pitch
    al = np.array(mask).astype(np.float32)[..., None] / 255.0
    arr = np.array(big).astype(np.float32) * (1 - al) + np.array(INK, np.float32) * al
    new = np.array(Image.fromarray(arr.clip(0, 255).astype(np.uint8)).resize((W, H), Image.BOX))
    # quantize changed pixels; never use palette entries that are transparent black
    P = tim.pal_rgb(pal); cand = np.where(pal != 0)[0]
    ch = np.abs(new.astype(int) - im.astype(int)).sum(2) > 0
    dd = ((new[ch].astype(int)[:, None, :] - P[cand][None]) ** 2).sum(2)
    nidx = idx.copy(); nidx[ch] = cand[dd.argmin(1)]
    t[pixoff:pixoff + nidx.size] = nidx.tobytes()
    Image.fromarray(tim.rgb(pal, nidx)).save(os.path.join(prev, name + '_en.png'))
    print(name, 'font', round(float(size), 2), 'lines', len(lines))
    return t

TEXT_OF = {'note1': NOTES[0], 'note2': NOTES[1]}
t0 = process(dec(C + hs), None, 'note1')
t1 = process(dec(C + st1), None, 'note2')
e0 = npk.encode_stream(bytes(t0)); e1 = npk.encode_stream(bytes(t1))
assert npk.lz_stream_decode(e0, 0, out_len=len(t0))[0] == bytes(t0)
assert npk.lz_stream_decode(e1, 0, out_len=len(t1))[0] == bytes(t1)
end = C + 16 + len(e0) + len(e1)
print('streams', len(e0), len(e1), 'container end', end, 'limit', LIMIT, '(orig', C + st1 + s1, ')')
assert end <= LIMIT
d[C:LIMIT] = struct.pack('<4I', 16, len(e0), 16 + len(e0), len(e1)) + e0 + e1 + b'\0' * (LIMIT - end)
open(dst, 'wb').write(d)
print('wrote', dst)
