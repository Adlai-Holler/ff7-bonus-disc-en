"""List Japanese strings still referenced (data pointer, lui pair, or gp-relative) in an exe."""
import sys, struct, unicodedata; sys.path.insert(0,'/home/claude/scripts'); import exe_tool
d=open(sys.argv[1],'rb').read(); N=len(d)
GP=0x800BAB30; T=0x80010200
gprefs={}
for i in range(0x800,0x70000,4):
    w=struct.unpack_from('<I',d,i)[0]; op=w>>26; rs=(w>>21)&31
    if rs==28 and op in (0x09,0x08,0x23,0x21,0x25,0x20,0x24,0x2b,0x29,0x28):
        imm=w&0xffff; imm-= 0x10000 if imm&0x8000 else 0
        gprefs.setdefault(GP+imm,[]).append(i)
cr=exe_tool.code_refs(d)
def is_jp(j):
    if j+1>=N: return False
    c=(d[j]<<8)|d[j+1]
    return (0x829F<=c<=0x82F1) or (0x8340<=c<=0x8396) or (0x889F<=c<=0x9FFC) or (0xE040<=c<=0xEAA4)
def scan(lo,hi):
    out=[]; i=lo; hi=min(hi,N-2)
    while i<hi:
        j=i; cnt=0
        while is_jp(j): j+=2; cnt+=1
        if cnt:
            w=i
            while w>0 and d[w-1]!=0: w-=1
            e=d.find(b'\0',j); e=N if e<0 else e
            # the real start may be anywhere from the previous NUL up to the first Japanese byte
            # (strings can sit right after a pointer word with no NUL between): take the first referenced one
            best=None
            for s in range(i,w-1,-1):
                a=T+s-0x800
                p=d.count(struct.pack('<I',a)); c=a in cr; g=len(gprefs.get(a,[]))
                if p or c or g: best=(s,p,c,g); break
            s=best[0] if best else i
            try: t=d[s:e].decode('shift_jis')
            except UnicodeDecodeError: t=None
            if t and all(unicodedata.category(ch)[0] in 'LNPSZ' for ch in t if ord(ch)>=0x20):
                out.append((s,t,best[1] if best else 0,best[2] if best else False,best[3] if best else 0))
                i=e+1
            else:
                i=j          # false start (e.g. pointer bytes that look like a kanji): keep scanning right after it
        else: i+=1
    return out
regions={'labels 0x800-0x9000':(0x800,0x9000),'text 0x70000-0x79AAC':(0x70000,0x79AAC),
         'scenes 0x79AAC-0x8F000':(0x79AAC,0x8F000),'gp window':(0xA3330,0xB3330)}
for name,(lo,hi) in regions.items():
    res=scan(lo,hi); live=[x for x in res if x[2] or x[3] or x[4]]
    print(f'{name}: JP strings {len(res)}, referenced {len(live)}')
    for s,t,p,c,g in live: print(f'   {s:#07x} {t!r} ptrs={p} code={c} gp={g}')
