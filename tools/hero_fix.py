"""MLIST item 1 (heroes, 418-byte records): weapon names + re-wrap blurbs (@0x62, 320 bytes) with newlines at 59 cols."""
import sys, re, textwrap; sys.path.insert(0, '/home/claude/mlist'); import mlist_tool as M
src, dst = sys.argv[1:3]
WEAP = {'Gimmick Arm': 'Gun-arm'}
it = M.decompress_file(open(src, 'rb').read()); s = bytearray(it[1]['data']); R = 418
for i in range(len(s) // R):
    o = i * R
    n = bytes(s[o:o+0x20]).split(b'\0')[0].decode('cp932')
    if n == 'Red XIII Nanaki': s[o:o+0x20] = 'Red XIII (Nanaki)'.encode('cp932').ljust(0x20, b'\0')
    w = bytes(s[o+0x52:o+0x62]).split(b'\0')[0].decode('cp932')
    if w in WEAP: s[o+0x52:o+0x62] = WEAP[w].encode().ljust(16, b'\0')
    t = bytes(s[o+0x62:o+R]).split(b'\0')[0].decode('cp932')
    t = re.sub(r'\s+', ' ', t.replace('\n', ' ')).strip()
    t = t.replace('Clouds childhood', "Cloud's childhood").replace('Aftera ', 'After a ').replace('developmentfunding', 'development funding')
    t = t.replace('in the ruined slums', 'in the run-down slums')
    t = t.replace('Until five years ago he was a Shinra SOLDIER admired by everyone. After learning his birth secret in Nibelheim he became a ruler.',
                  'Until five years ago he was the Shinra SOLDIER everyone admired. On learning the secret of his birth in Nibelheim, he went from hero to tyrant.')
    t = re.sub(r'([.!?])([A-Z])', r'\1 \2', t)
    b = '\n'.join(textwrap.wrap(t, 59, break_long_words=False)).encode('cp932'); assert len(b) < R - 0x62
    s[o+0x62:o+R] = b.ljust(R - 0x62, b'\0'); print(i, b.decode().replace('\n', ' / '))
items = [bytes(x['data']) for x in it]; items[1] = bytes(s)
open(dst, 'wb').write(M.build_file(items, [(x['off'], x['nblocks']) for x in it], verbose=True))
