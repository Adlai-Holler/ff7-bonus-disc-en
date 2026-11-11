"""Re-sort MLIST for English: location list (item 2) alphabetical, monster area refs remapped,
and write namesort.bin (296 x u32 record indices in English A-Z order) for the EXE's name sort."""
import sys, struct, re
sys.path.insert(0,'/home/claude/mlist'); import mlist_tool as M
src, dst, nsort = sys.argv[1:4]
it = M.decompress_file(open(src,'rb').read())
items = [bytearray(x['data']) for x in it]; layout = [(x['off'], x['nblocks']) for x in it]
def key(s):
    s = s.lower(); s = re.sub(r'^(the )', '', s)
    return [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', re.sub(r'[^a-z0-9 ]', '', s))]
REN = {'Grassland Area (Marsh)': 'Grassland (Marsh)', 'Mako Cannon (Sister Ray)': 'Sister Ray Cannon',
       'Underwater Mako Reactor': 'Underwater Reactor', 'Sector 4 Underground Mine': 'Sector 4 Underground'}
for i in range(75):     # area grid column is ~21 chars wide
    n = bytes(items[2][i*32:i*32+32]).split(b'\0')[0].decode('cp932')
    if n in REN: items[2][i*32:i*32+32] = REN[n].encode('cp932').ljust(32, b'\0')
loc = items[2]; names = [bytes(loc[i*32:i*32+32]) for i in range(75)]
txt = [n.split(b'\0')[0].decode('cp932') for n in names]
LAST = ['Various', 'Air, etc.', '????']
order = sorted([i for i in range(75) if txt[i] not in LAST], key=lambda i: key(txt[i])) + [txt.index(t) for t in LAST]
new_of = {old: new for new, old in enumerate(order)}
items[2] = bytearray(b''.join(names[o] for o in order))
mon = items[0]
for r in range(296):
    b = r*724; n = struct.unpack_from('<I', mon, b+660)[0]
    for k in range(n):
        o = struct.unpack_from('<I', mon, b+664+4*k)[0]; struct.pack_into('<I', mon, b+664+4*k, new_of[o])
mn = [bytes(mon[r*724:r*724+32]).split(b'\0')[0].decode('cp932') for r in range(296)]
ns = sorted(range(296), key=lambda r: (key(mn[r]), r))
open(nsort, 'wb').write(struct.pack('<296I', *ns))
open(dst, 'wb').write(M.build_file([bytes(x) for x in items], layout))
print('areas:', [txt[o] for o in order])
print('names:', [mn[r] for r in ns[:15]], '...', [mn[r] for r in ns[-5:]])
