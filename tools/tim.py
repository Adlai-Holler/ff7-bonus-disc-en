import struct
import numpy as np
def parse(t):
    clen = struct.unpack_from('<I', t, 8)[0]; cw, ch = struct.unpack_from('<HH', t, 16)
    pal = np.array([struct.unpack_from('<H', t, 20 + 2 * i)[0] for i in range(cw * ch)], dtype=np.uint16)
    o = 8 + clen; iw, ih = struct.unpack_from('<HH', t, o + 8); W = iw * 2
    idx = np.frombuffer(t, dtype=np.uint8, count=W * ih, offset=o + 12).reshape(ih, W).copy()
    return pal, idx, o + 12
def pal_rgb(pal):
    return np.stack([(pal & 31) << 3, ((pal >> 5) & 31) << 3, ((pal >> 10) & 31) << 3], 1).astype(np.int32)
def rgb(pal, idx): return pal_rgb(pal)[idx].astype(np.uint8)
def nearest(pal, img):
    """map RGB image to nearest palette index (ignores index 0 if it is the transparent black)"""
    P = pal_rgb(pal); flat = img.reshape(-1, 3).astype(np.int32)
    d = ((flat[:, None, :] - P[None, :, :]) ** 2).sum(2)
    return d.argmin(1).astype(np.uint8).reshape(img.shape[:2])

def view(t):
    """RGB array for any TIM (4/8/16 bpp). Uses the first CLUT row. For inspection only."""
    flags = struct.unpack_from('<I', t, 4)[0]; pmode = flags & 3; has_clut = flags & 8
    o = 8; pal = None
    if has_clut:
        clen = struct.unpack_from('<I', t, o)[0]; cw, ch = struct.unpack_from('<HH', t, o + 8)
        pal = np.array(struct.unpack_from(f'<{cw}H', t, o + 12), dtype=np.uint16); o += clen
    iw, ih = struct.unpack_from('<HH', t, o + 8); data = np.frombuffer(t, np.uint8, count=iw * 2 * ih, offset=o + 12)
    if pmode == 0:
        b = data.reshape(ih, iw * 2); idx = np.empty((ih, iw * 4), np.uint8); idx[:, 0::2] = b & 15; idx[:, 1::2] = b >> 4
        return pal_rgb(pal)[idx].astype(np.uint8)
    if pmode == 1:
        return pal_rgb(pal)[data.reshape(ih, iw * 2)].astype(np.uint8)
    px = data.view('<u2').reshape(ih, iw)
    return np.stack([(px & 31) << 3, ((px >> 5) & 31) << 3, ((px >> 10) & 31) << 3], -1).astype(np.uint8)
