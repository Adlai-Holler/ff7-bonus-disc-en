"""Restore the full Japanese column of text/exe_strings.tsv from your own disc.

usage: python3 tools/fill_jp.py <original SLPS_010.60> [in.tsv] [out.tsv]

Longer passages in the published table are stored as 'crc32:xxxxxxxx'. This
replaces each one with the Japanese text read from your EXE, after checking the
checksum, so you can review the translation side by side.
"""
import sys, zlib, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from exe_tool import decode

exe = open(sys.argv[1], 'rb').read()
src = sys.argv[2] if len(sys.argv) > 2 else 'text/exe_strings.tsv'
dst = sys.argv[3] if len(sys.argv) > 3 else 'text/exe_strings_full.tsv'
rows = open(src, encoding='utf-8').read().split('\n')
out, n = [rows[0]], 0
for r in rows[1:]:
    f = r.split('\t')
    if len(f) > 4 and f[3].startswith('crc32:'):
        o, ln = int(f[0], 16), int(f[1])
        b = exe[o:o + ln]
        if '%08x' % zlib.crc32(b) != f[3][6:]:
            sys.exit(f'checksum mismatch at {f[0]}: this is not the original SLPS-01060 EXE')
        f[3] = decode(b)[0]; n += 1
    out.append('\t'.join(f))
open(dst, 'w', encoding='utf-8').write('\n'.join(out))
print(f'restored {n} Japanese strings -> {dst}')
