"""Overlay font: renders a proportional 4bpp glyph sheet for the PSX 512x240 page screen.
Pixels on that screen are ~0.63 as wide as tall, so glyphs are rendered stretched horizontally (XS)."""
from PIL import Image, ImageDraw, ImageFont
import os
FONT = os.environ.get('OVFONT', '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf')
FONTB = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'
SIZE = float(os.environ.get('OVSIZE', '9')); XS = float(os.environ.get('OVXS', '1.6'))
EMB = int(os.environ.get('OVEMB', '2'))
PIX = int(os.environ.get('OVPIX', '0'))
MONO = os.environ.get('OVMONO', '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf')   # 1-bit hinted, no stretch: matches the game's own text boxes
MONOSZ = int(os.environ.get('OVMONOSZ', '13'))
TRACK = int(os.environ.get('OVTRACK', '1'))     # extra letter spacing, like the game's own text boxes      # 1 = hand-drawn pixel font (pixfont.py)
import sys as _sys; _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import pixfont
GH = 15                       # glyph cell height incl. 1px shadow
ASC = 11                      # baseline row
SYM = {0x80: '△', 0x81: '○', 0x82: '×', 0x83: '□', 0x84: '’', 0x85: '…', 0x86: '•', 0x87: '→', 0x88: '★', 0x89: '♪', 0x8A: '◯', 0x8B: '━', 0x8C: ' '}
CHARS = [chr(c) for c in range(32, 127)]
def codes():
    return [(ord(c), c) for c in CHARS] + sorted(SYM.items())

def render_glyph(ch, font):
    big = 4                                  # supersample
    W = 40 * big; H = GH * big
    im = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(im)
    f = font
    asc, desc = f.getmetrics()
    dr.text((2 * big, ASC * big - asc), ch, fill=255, font=f)
    for k in range(1, EMB + 1):          # synthetic emboldening: thicken vertical strokes before the anamorphic squeeze
        dr.text((2 * big + k, ASC * big - asc), ch, fill=255, font=f)
    # horizontal stretch
    bbox = im.getbbox()
    adv = f.getlength(ch) * XS / big
    if ch == ' ': return None, max(3, round(adv))
    if bbox is None:
        return None, round(adv)
    x0 = bbox[0]; x1 = bbox[2]
    crop = im.crop((x0, 0, x1, H))
    w = max(1, round((x1 - x0) * XS / big))
    small = crop.resize((w, GH), Image.BOX)
    return small, max(w + 1, round(adv))

_mono = None
def mono_glyph(ch):
    global _mono
    if _mono is None: _mono = ImageFont.truetype(MONO, MONOSZ)
    f = _mono; asc, desc = f.getmetrics()
    adv = int(round(f.getlength(ch)))
    if ch == ' ': return None, adv + TRACK
    im = Image.new('L', (adv + 6, GH), 0); dr = ImageDraw.Draw(im); dr.fontmode = '1'
    dr.text((2, ASC - asc), ch, fill=255, font=f)
    bb = im.getbbox()
    if bb is None: return None, adv
    crop = im.crop((bb[0], 0, bb[2], GH))
    return crop, max(adv, bb[2] - bb[0] + 1) + TRACK

def tri(): # hand-drawn △ (triangle button symbol), 9 wide
    rows = ["....#....", "...#.#...", "...#.#...", "..#...#..", "..#...#..", ".#.....#.", ".#######.", "........."]
    return rows

PAL_ICON = [(0,0,0), (14,14,40), (60,60,140), (100,100,185), (160,160,228), (16,110,46), (40,196,84), (130,240,160), (8,48,30)]

ICON_ROWS = """.....ooooooo.....
..ooolllllllooo..
.oolllllgllllloo.
oobbbbbhggbbbbboo
obbbbbhhkggbbbbbo
obbbbhhkkkggbbbbo
obbbhhkkkkkggbbbo
oodgggggggggggdoo
.oodGGGGGGGGGdoo.
..ooodddddddooo..
.....ooooooo.....""".split()

def icon_glyph():
    # hand-pixelled round triangle button (17x11 screen px = round on the 0.625-aspect page screen)
    out = Image.new('P', (17, GH), 0)
    for y, r in enumerate(ICON_ROWS):
        for x, c in enumerate(r):
            v = '.odblGghk'.index(c)
            if v: out.putpixel((x, y + 1), v)
    return out

SLOT_ROWS = ["..555555..",
             ".55....55.",
             "55......55",
             "55......55",
             "55......55",
             "55......55",
             ".55....55.",
             "..555555.."]
SLOT_TOP = 3          # cell row of the socket's top: centred on capital height

def slot_glyph():
    # hand-pixelled materia socket (white palette indices: 5 rim, 1 dark hole, 4 glint) - crisp like the text
    im = Image.new('P', (len(SLOT_ROWS[0]), GH), 0); im.info['pal'] = 0
    for y, r in enumerate(SLOT_ROWS):
        for x, c in enumerate(r):
            if c != '.': im.putpixel((x, y + SLOT_TOP), int(c))
    return im

def link_glyph():
    im = Image.new('P', (4, GH), 0); im.info['pal'] = 0
    for y in (SLOT_TOP + 3, SLOT_TOP + 4):
        for x in range(4): im.putpixel((x, y), 5)
    return im

def build():
    font = ImageFont.truetype(FONT, int(SIZE * 4))
    glyphs = {}
    for code, ch in codes():
        if code == 0x80: glyphs[code] = (icon_glyph(), 19); continue
        if code == 0x8A: glyphs[code] = (slot_glyph(), 10); continue
        if code == 0x8B: glyphs[code] = (link_glyph(), 4); continue
        if code == 0x8C: glyphs[code] = (None, 4); continue        # thin space between slot groups
        if PIX and ch in pixfont.G:
            rows, w = pixfont.wide(ch); im = Image.new('L', (max(1, w), GH), 0)
            for y, r in enumerate(rows):
                for x, v in enumerate(r):
                    if v: im.putpixel((x, y + 3), 255)
            glyphs[code] = ((im if ch != ' ' else None), w + 2 if ch != ' ' else 4); continue
        if MONO and ch.isprintable() and code < 0x80 or ch in '’…•→':
            glyphs[code] = mono_glyph(ch); continue
        glyphs[code] = render_glyph(ch, font)
    # pack into consecutive 256-texel strips, one glyph row (GH+1 tall); strip k = its own 4bpp texture page
    x = 0; table = {}; pix = {}; strip = 0
    for code, (im, adv) in glyphs.items():
        if im is None: table[code] = (0, 0, 0, adv, 0, 0); continue
        w = im.size[0] + 1
        if im.mode == 'P':
            if (x % 256) + w > 256: x = (x // 256 + 1) * 256
            for yy in range(GH):
                for xx in range(im.size[0]):
                    v = im.getpixel((xx, yy))
                    if v: pix[(x + xx, yy)] = v
            if im.info.get('pal', 4) == 0:          # text-coloured symbols (slots) get the text's drop shadow
                for yy in range(GH):
                    for xx in range(im.size[0]):
                        if im.getpixel((xx, yy)) and (x + xx + 1, yy + 1) not in pix and yy + 1 < GH + 1:
                            pix[(x + xx + 1, yy + 1)] = 1
            table[code] = (x % 256, 0, w, adv, x // 256, im.info.get('pal', 4)); x += w + 1; continue
        if (x % 256) + w > 256: x = (x // 256 + 1) * 256
        a = im.load()
        for yy in range(GH):
            for xx in range(im.size[0]):
                v = a[xx, yy]
                lvl = 0 if v < 75 else 2 if v < 120 else 3 if v < 180 else 4 if v < 230 else 5
                if lvl: pix[(x + xx, yy)] = lvl
        for yy in range(GH):
            for xx in range(im.size[0]):
                if a[xx, yy] >= 110:
                    p = (x + xx + 1, yy + 1)
                    if p not in pix: pix[p] = 1
        table[code] = (x % 256, 0, w, adv, x // 256, 0)
        x += w + 1
    nstrips = x // 256 + 1
    sheet = Image.new('P', (256 * nstrips, GH + 1), 0)
    for (px, py), v in pix.items(): sheet.putpixel((px, py), v)
    return sheet, table

PAL_WHITE = [(0,0,0), (8,8,16), (110,110,120), (160,160,168), (210,210,215), (248,248,248)]
PAL_GOLD  = [(0,0,0), (8,8,16), (120,100,40), (170,145,60), (215,190,90), (248,224,120)]
PAL_CYAN  = [(0,0,0), (8,8,16), (60,110,130), (90,160,180), (130,205,225), (170,235,250)]

def bgr555(c, idx):
    r, g, b = c
    if idx == 0: return 0
    v = (r >> 3) | ((g >> 3) << 5) | ((b >> 3) << 10)
    return v or 0x8000 if idx else v       # STP bit keeps black opaque

def clut_words():
    out = []
    for pal in (PAL_WHITE, PAL_GOLD, PAL_CYAN, PAL_ICON):
        row = [bgr555(c, i) for i, c in enumerate(pal)] + [0] * (16 - len(pal))
        out.append(row)
    return out

def pack4(sheet):
    w, h = sheet.size; b = bytearray()
    p = sheet.load()
    for y in range(h):
        for x in range(0, w, 2):
            b.append((p[x, y] & 15) | ((p[x + 1, y] & 15) << 4))
    return bytes(b)

def measure(table, s):
    return sum(table.get(ord(c) if ord(c) < 128 else c, (0,0,0,6))[3] for c in s)
