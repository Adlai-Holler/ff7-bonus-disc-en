"""Raw 2336-byte-sector STR access (mkpsxiso-extracted XA files)."""
import struct
S = 2336
class STR:
    def __init__(self, path):
        self.b = bytearray(open(path, 'rb').read()); self.n = len(self.b) // S
        self.frames = {}          # frame number -> list of (sector index, chunk, nchunks, size)
        for i in range(self.n):
            d = self.b[i * S + 8:i * S + 8 + 2048]
            if d[:4] != b'\x60\x01\x01\x80': continue
            ch, nch, fn, size = struct.unpack_from('<HHII', d, 4)
            self.frames.setdefault(fn, []).append((i, ch, nch, size))
    def frame(self, fn):
        secs = sorted(self.frames[fn], key=lambda t: t[1])
        data = b''.join(bytes(self.b[i * S + 8 + 32:i * S + 8 + 2048]) for i, _, _, _ in secs)
        return data[:secs[0][3]]
    def capacity(self, fn): return len(self.frames[fn]) * 2016
    def put(self, fn, data):
        secs = sorted(self.frames[fn], key=lambda t: t[1])
        assert len(data) <= len(secs) * 2016, (fn, len(data), len(secs) * 2016)
        data = data + b'\0' * ((-len(data)) % 4)
        for i, ch, nch, _ in secs:
            o = i * S + 8
            struct.pack_into('<I', self.b, o + 12, len(data))
            chunk = data[ch * 2016:(ch + 1) * 2016]
            self.b[o + 32:o + 2048] = chunk + b'\0' * (2016 - len(chunk))
        # header words that mirror the frame header (bytes 0x14.. in sector hdr): rlc count + 0x3800 + q + ver
        for i, ch, nch, _ in secs:
            o = i * S + 8
            self.b[o + 0x14:o + 0x14 + 8] = data[:8]

def wrap2352(sectors_bytes):
    sync = bytes([0] + [0xff] * 10 + [0]) + bytes([0, 0, 0, 2])
    return b''.join(sync + sectors_bytes[i:i + S] for i in range(0, len(sectors_bytes), S))
