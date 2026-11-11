"""Replace the Japanese description lines of the PP07FFE.STR intro timeline with English.
usage: str_intro.py <in STR> <out STR> <preview dir>"""
import sys, os, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, '/home/claude/scripts')
import mdec, strio

src, dst, prev = sys.argv[1:4]
os.makedirs(prev, exist_ok=True)
FB = '/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf'
TEXTCOL = 205          # same grey as the date stamps
# screens: frame range (0-based decoded index), gap frames for the clean plate, bands to replace
SCREENS = [
 dict(frames=(8, 109), gap=(110, 127), bands=[
   dict(y=(56, 84), lines=[(12.5, 'Shinra Company discovers Mako energy')]),
   dict(y=(139, 166), lines=[(12, 'First Mako Reactor power plant built'), (12, 'Reactors soon spread across the world')])]),
 dict(frames=(128, 229), gap=(230, 247), bands=[
   dict(y=(57, 87), lines=[(12, "Midgar, the world's largest Mako city, is built"), (12, 'Shinra headquarters established there')]),
   dict(y=(141, 167), lines=[(12, 'Conflict deepens with the'), (12, 'anti-Shinra group AVALANCHE')])]),
 dict(frames=(248, 349), gap=(350, 373), bands=[
   dict(y=(60, 85), lines=[(12.5, "AVALANCHE's leader assassinated")]),
   dict(y=(140, 187), lines=[(12, 'Shinra and AVALANCHE are'), (21, 'ON THE BRINK'), (12, 'of all-out war')])]),
]
S = 4

def decode_all(path, nframes):
    raw = '/tmp/_intro.raw'
    s = strio.STR(path)
    last = max(i for fr in range(1, nframes + 1) for i, _, _, _ in s.frames[fr])
    open(raw, 'wb').write(strio.wrap2352(bytes(s.b[:(last + 1) * strio.S])))
    out = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'psxstr', '-i', raw, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         capture_output=True).stdout
    return s, np.frombuffer(out, np.uint8).reshape(-1, 224, 320, 3)[:nframes].copy()

def layer(band):
    """English text, one entry per line: (alpha, glow, reveal start, reveal end, x0, x1) in 320x224 space.
    Each line has its own layer so a line's ascenders/descenders never borrow another line's reveal timing."""
    y0, y1 = band['y']; lines = band['lines']
    fonts = [ImageFont.truetype(FB, int(sz * S)) for sz, _ in lines]
    hs = [f.getbbox('Ag')[3] - f.getbbox('Ag')[1] + sz * S * 0.12 for f, (sz, _) in zip(fonts, lines)]
    tot = sum(hs); y = ((y0 + y1) / 2) * S - tot / 2
    tmp = ImageDraw.Draw(Image.new('L', (8, 8)))
    widths = [tmp.textlength(t, font=f) for f, (_, t) in zip(fonts, lines)]
    total_w = sum(widths); acc = 0; out = []
    for f, (sz, t), h, w in zip(fonts, lines, hs, widths):
        x = 160 * S - w / 2
        assert x >= 4 * S, ('too wide', t, w / S)
        big = Image.new('L', (320 * S, 224 * S), 0)
        ImageDraw.Draw(big).text((x, y - f.getbbox('Ag')[1]), t, fill=255, font=f)
        a = np.asarray(big.resize((320, 224), Image.BOX)).astype(np.float32) / 255
        glow = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
        out.append((a, glow, acc / total_w, (acc + w) / total_w, x / S, (x + w) / S))
        acc += w; y += h
    return out

def main():
    nfr = SCREENS[-1]['gap'][1] + 1
    s, fr = decode_all(src, nfr)
    out = fr.copy()
    touched = set()
    for sc in SCREENS:
        f0, f1 = sc['frames']; g0, g1 = sc['gap']
        plate = np.median(fr[g0:g1 + 1].astype(np.float32), axis=0)
        for band in sc['bands']:
            y0, y1 = band['y']
            parts = layer(band)
            base = np.median([(fr[g, y0:y1 + 1].max(2) > 70).sum() for g in range(g0, g1 + 1)])   # stars only
            final = (fr[f1 - 4, y0:y1 + 1].max(2) > 70).sum() - base
            rmax = 0.0
            xs = np.arange(320)[None, :]
            for t in range(f0, f1 + 1):
                cnt = (fr[t, y0:y1 + 1].max(2) > 70).sum()
                rr = (cnt - base) / max(1, final)
                if rr < 0.04: rr = 0.0                                  # nothing typed yet (just stars)
                r = rmax = max(rmax, min(1.0, rr))
                if t > f1 - 12 and r > 0.9: r = 1.0
                img = out[t].astype(np.float32)
                img[y0:y1 + 1] = plate[y0:y1 + 1]
                for a, glow, r0, r1, lx0, lx1 in parts:
                    if r <= r0 + 0.005: continue
                    lr = min(1.0, (r - r0) / (r1 - r0))              # this line's own reveal fraction
                    edge = lx0 + lr * (lx1 - lx0 + 6)
                    vis = np.clip((edge - xs) / 4.0, 0, 1)
                    al = (a * vis)[..., None]; gl = (glow * vis * 0.45)[..., None]
                    img = img * (1 - gl * 0.6) + TEXTCOL * gl * 0.6
                    img = img * (1 - al) + TEXTCOL * al
                out[t] = np.clip(img, 0, 255).astype(np.uint8)
                touched.add(t)
    for t in sorted(touched):
        if t in (60, 105, 180, 225, 300, 345): Image.fromarray(out[t]).resize((640, 448), Image.LANCZOS).save(f'{prev}/f{t:03d}.png')
    np.save(prev + '/out.npy', out)
    # encode & store
    sizes = []
    for t in sorted(touched):
        fn = t + 1
        for q in (1, 2, 3, 4, 6):
            data, _ = mdec.encode_frame(out[t], q)
            if len(data) <= s.capacity(fn): break
        s.put(fn, data); sizes.append((fn, q, len(data), s.capacity(fn)))
    open(dst, 'wb').write(s.b)
    print('re-encoded', len(sizes), 'frames; q used', sorted(set(q for _, q, _, _ in sizes)),
          'max fill %.2f' % max(n / c for _, _, n, c in sizes))
    # verify by decoding the output
    _, chk = decode_all(dst, nfr)
    err = np.abs(chk[sorted(touched)].astype(int) - out[sorted(touched)].astype(int)).mean()
    print('decode check mean abs err %.2f' % err)
    for t in (60, 180, 345):
        Image.fromarray(chk[t]).resize((640, 448), Image.LANCZOS).save(f'{prev}/dec{t:03d}.png')
main()
