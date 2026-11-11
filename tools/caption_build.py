"""Field-scene caption prototype: replace the two Japanese captions at the bottom of FF_TTOWN.NPK scene images.
usage: caption_build.py <in FF_TTOWN.NPK> <out FF_TTOWN.NPK> <preview_dir> <captions.json>
captions.json: {"<scene index>": ["Left caption", "Right caption"], ...}  (scene index = order of image chains)"""
import sys, os, struct, json, pickle
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, '/home/claude/scripts')
import npk

src, dst, prev, capf = sys.argv[1:5]
d = bytearray(open(src, 'rb').read())
caps = {int(k): v for k, v in json.load(open(capf, encoding='utf-8')).items()}
info = pickle.load(open('/home/claude/npk/town/tt_info.pkl', 'rb'))        # (k, offset, nblocks, w, h, pmode)
CLEAN = np.load('/home/claude/npk/town/strip_clean.npy').astype(np.float32)  # rows 196..239, frame without text
Y0 = 196
FONT = os.environ.get('CAPFONT', '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf')
HX = float(os.environ.get('HX', '1.6')); S = 4
SIZE = float(os.environ.get('CAPSIZE', '17'))
SDX, SDY = float(os.environ.get('SDX', '3')), float(os.environ.get('SDY', '2'))
SDARK = float(os.environ.get('SDARK', '0.35'))
BOXES = {'L': (20, 238, 125.0), 'R': (262, 498, 357.0)}   # x0, x1, centre
TY0, TY1 = 207, 238                                      # caption band (below the picture's bottom edge)

def fill_holes(clean):
    """pixels that were text on every page come out black in CLEAN: inpaint them"""
    m = (clean.sum(2) < 12).astype(np.uint8)
    m[:8] = 0
    return cv2.inpaint(clean.clip(0, 255).astype(np.uint8), m, 3, cv2.INPAINT_TELEA).astype(np.float32)
CLEAN = fill_holes(CLEAN)

def decode16(t):
    flags = struct.unpack_from('<I', t, 4)[0]; assert flags & 3 == 2 and not flags & 8
    w, h = struct.unpack_from('<HH', t, 16); px = np.frombuffer(t, '<u2', count=w * h, offset=20).reshape(h, w).copy()
    rgb = np.stack([(px & 31) << 3, ((px >> 5) & 31) << 3, ((px >> 10) & 31) << 3], -1).astype(np.float32)
    return px, rgb

def draw(img, label, side):
    x0, x1, cx = BOXES[side]; H, W = img.shape[:2]
    size = SIZE
    while True:
        f = ImageFont.truetype(FONT, int(size * S))
        tw = f.getlength(label) * HX / S
        if tw <= (x1 - x0) - 6 or size <= 9: break
        size -= 0.25
    bb = f.getbbox('Mg'); top = bb[1] / S; ih = (f.getbbox('M')[3] - bb[1]) / S
    tx = cx - tw / 2; ty = (TY0 + TY1) / 2 - ih / 2 - top + 1
    tmp = Image.new('L', (int(f.getlength(label)) + 8 * S, int(size * S * 1.6)), 0)
    ImageDraw.Draw(tmp).text((0, 0), label, font=f, fill=255)
    tmp = tmp.resize((int(tmp.width * HX), tmp.height), Image.LANCZOS)
    def alpha(dx, dy, blur=0):
        m = Image.new('L', (W * S, H * S), 0); m.paste(tmp, (int((tx + dx) * S), int((ty + dy) * S)))
        a = np.array(m).astype(np.float32)
        if blur: a = cv2.GaussianBlur(a, (0, 0), blur * S)
        return a / 255.0
    big = np.array(Image.fromarray(img.clip(0, 255).astype(np.uint8)).resize((W * S, H * S), Image.NEAREST)).astype(np.float32)
    sh = alpha(SDX, SDY, 0.5)[..., None]
    big = big * (1 - sh * (1 - SDARK))
    al = alpha(0, 0)[..., None]
    yy = (np.arange(H * S)[:, None] / S - (ty + top)) / max(ih, 1)
    t = np.clip(yy, 0, 1)[..., None]
    col = np.array([236, 236, 236], np.float32) * (1 - t) + np.array([176, 176, 172], np.float32) * t
    big = big * (1 - al) + col * al
    return np.array(Image.fromarray(big.clip(0, 255).astype(np.uint8)).resize((W, H), Image.BOX)).astype(np.float32), size

for k, (lcap, rcap) in sorted(caps.items()):
    _, off, nblk, w, h, pm = info[k]
    t = bytearray(npk.game_decode(bytes(d), off))
    px, rgb = decode16(t)
    out = rgb.copy()
    band = slice(TY0, TY1 + 1)
    strip = out[band]; cl = CLEAN[TY0 - Y0:TY1 - Y0 + 1]
    diff = np.abs(strip - cl).sum(2)
    m = np.zeros(diff.shape, bool)
    for side, (x0, x1, _) in BOXES.items():
        m[:, x0:x1] = diff[:, x0:x1] > 36
    m = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
    for side, (x0, x1, _) in BOXES.items():     # keep the dilation inside the boxes
        pass
    strip[m] = cl[m]; out[band] = strip
    sizes = []
    for lab, side in ((lcap, 'L'), (rcap, 'R')):
        out, sz = draw(out, lab, side); sizes.append(sz)
    # back to 15-bit, keep each pixel's STP bit, avoid the transparent 0x0000
    q = (out.clip(0, 255) / 8 + 0.5).astype(np.int32).clip(0, 31)
    npx = (q[..., 0] | (q[..., 1] << 5) | (q[..., 2] << 10)).astype(np.uint16) | (px & 0x8000)
    changed = np.abs(out - rgb).sum(2) > 0.5
    npx[(npx == 0) & changed] = 1 << 10
    newpx = np.where(changed, npx, px)
    t[20:20 + newpx.size * 2] = newpx.astype('<u2').tobytes()
    enc = npk.encode_blocks(bytes(t), nblk)
    assert npk.game_decode(enc + b'\0' * 2048, 0) == bytes(t)
    slot = ((nblk * 1024 + 2047) // 2048) * 2048
    assert len(enc) <= slot, (k, len(enc), slot)
    d[off:off + slot] = enc + b'\0' * (slot - len(enc))
    vis = np.stack([(newpx & 31) << 3, ((newpx >> 5) & 31) << 3, ((newpx >> 10) & 31) << 3], -1).astype(np.uint8)
    Image.fromarray(vis).save(os.path.join(prev, f'cap_{k:03d}.png'))
    print(k, lcap, '|', rcap, 'font', sizes, 'blocks', len(enc) // 1024, '/', nblk)
open(dst, 'wb').write(d)
print('wrote', dst)
