"""Word-wrap MLIST summon blurbs (item 9, 284-byte records, text @+0x54, 200 bytes) at 59 cols."""
import sys, textwrap; sys.path.insert(0, '/home/claude/mlist'); import mlist_tool as M
src, dst = sys.argv[1:3]
EDIT = {  # small trims so item 9 still fits its 2 compressed blocks (newlines compress worse than spaces)
 'He deals damage with the powerful breath attack "Mega Flare."': 'He attacks with the powerful breath "Mega Flare."',
 'He deals damage with two kinds of attack: a breath attack and a ceiling-drop attack.': 'He attacks twice: a breath attack and a ceiling-drop.',
}
# official NA names (summon names @+0, attack names @+0x16, both 22-byte fields; also used in blurbs)
NAMES = [('Chocobo & Mog', 'Choco/Mog'), ('Special Move!!', 'DeathBlow!!'), ('Fat Chocobo', 'Fat-Chocobo'),
         ('Zantetsuken', 'Steel Bladed Sword'), ('Gungnir', 'Gunge Lance'), ('Terra Flare', 'Tera Flare')]
it = M.decompress_file(open(src, 'rb').read())
s = bytearray(it[9]['data'])
for i in range(len(s) // 284):
    for fo in (0, 0x16):
        t = bytes(s[i*284+fo:i*284+fo+22]).split(b'\0')[0].decode('cp932')
        for a, b in NAMES: t = t.replace(a, b)
        s[i*284+fo:i*284+fo+22] = t.encode('cp932').ljust(22, b'\0')[:22]
    o = i * 284 + 0x54; t = bytes(s[o:o+200]).split(b'\0')[0].decode('cp932').replace('\n', ' ')
    for a, b in EDIT.items(): t = t.replace(a, b)
    for a, b in NAMES: t = t.replace(a, b)
    t = t.replace('the "Gunge Lance" spear', 'the "Gunge Lance"')
    b = '\n'.join(textwrap.wrap(t, 59, break_long_words=False)).encode('cp932'); assert len(b) < 200
    s[o:o+200] = b.ljust(200, b'\0')
items = [bytes(x['data']) for x in it]; items[9] = bytes(s)
open(dst, 'wb').write(M.build_file(items, [(x['off'], x['nblocks']) for x in it], verbose=True))
