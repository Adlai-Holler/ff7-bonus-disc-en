"""Rebuild a modified block-chain NPK so it differs from the original as little as possible.

usage: npk_mindiff.py <original.NPK> <modified.NPK> <out.NPK> <tt_info.pkl>

For every scene chain listed in tt_info, the decoded image of <modified> is kept,
but the original compressed blocks are reused for the part of the image that did
not change; only the blocks after the first changed byte are re-encoded. The game
decodes identical pixels; a sector/byte-level patch against the original shrinks
to roughly the changed part of each image.
"""
import sys, pickle, struct
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import npk

orig_p, mod_p, out_p, info_p = sys.argv[1:5]
A = open(orig_p, 'rb').read()
B = open(mod_p, 'rb').read()
assert len(A) == len(B)
out = bytearray(B)
info = pickle.load(open(info_p, 'rb'))
kept = total = 0
for k, o, n, w, h, pm in info:
    na, nb = struct.unpack_from('<I', A, o)[0], struct.unpack_from('<I', B, o)[0]
    span = max(na, nb) * 1024
    if A[o:o + span] == B[o:o + span]:
        continue
    da, db = npk.game_decode(A, o), npk.game_decode(B, o)
    if da == db:
        out[o:o + na * 1024] = A[o:o + na * 1024]; kept += na; total += na; continue
    first = next((i for i in range(min(len(da), len(db))) if da[i] != db[i]), min(len(da), len(db)))
    # keep whole original blocks that end at or before the first changed byte
    blocks = npk.chain_blocks(A, o)
    pos = 0; keep = 0
    for bo, produced in blocks:
        if pos + produced > first: break
        pos += produced; keep += 1
    keep = min(keep, nb - 1)
    while True:
        try:
            tail = npk.encode_tail(db, pos, nb - keep)
            break
        except ValueError:
            if keep == 0: raise
            keep -= 1; pos -= blocks[keep][1]
    # prefix headers hold "blocks remaining" = n - index; valid only if counts match
    assert na == nb or keep == 0, (k, na, nb)
    new = A[o:o + keep * 1024] + tail
    seg = bytearray(B[o:o + nb * 1024]); seg[:len(new)] = new
    test = bytes(out[:o]) + bytes(seg) + bytes(out[o + nb * 1024:])
    assert npk.game_decode(test, o) == db, k
    out[o:o + nb * 1024] = seg
    kept += keep; total += nb
open(out_p, 'wb').write(out)
print(f'scenes: reused {kept} of {total} blocks ({100 * kept / max(total, 1):.0f}%)')
