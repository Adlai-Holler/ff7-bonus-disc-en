#!/usr/bin/env python3
"""
MLIST.LPK tool - FF7 Perfect Guide bonus disc (PSX)

FILE FORMAT
-----------
The file is a sequence of ITEMS, each starting on a 2048-byte (CD sector) boundary.
An item is a chain of 1024-byte BLOCKS compressed with LZSS:
  block header (8 bytes):  u32 blocks_remaining_in_item (N..1)
                           u16 end_offset  (compressed bytes used, counted from block start, incl. header)
                           u16 raw_size    (decompressed bytes produced by this block)
  then LZSS stream: flag byte (LSB first, 1=literal byte, 0=2-byte token), 8 entries per flag.
  token: b0 = pos low8, b1 = (pos high4 << 4) | (len-3)   -> len 3..18, pos = ABSOLUTE index into a
  4096-byte ring buffer.  Ring starts zeroed with write pointer at 4078 at the start of each ITEM and
  CONTINUES across the blocks of an item.  Unused tail of a block / sector is zero padding.
Decompressed items:
  0: 296 monster records x 724 bytes      3-8: u32 sort/index tables (not text)
  1: 10 character records x 418 bytes     2: 75 location names x 32 bytes
  9: 18 summon records x 284 bytes
All text is Shift-JIS, NUL-terminated inside fixed-size fields.
"""
import struct, sys, re, csv, os

N=4096; F=18; THR=3; R0=4078

# ------------------------------------------------------------------ layout
MON_RS=724
MON_FIELDS=[ # (offset, size, name, split_on_slash)
 (0x000,0x20,'name',False),(0x020,4,'lv',False),(0x024,10,'hp',False),(0x02e,6,'mp',False),
 (0x034,8,'exp',False),(0x03c,6,'ap',False),(0x042,6,'gil',False),
 (0x048,0x40,'itemA',True),(0x088,0x40,'itemB',True),(0x0c8,0x20,'itemC',True),
 (0x0e8,0x80,'element',True),(0x168,0xb4,'status',True),
 (0x21c,0x28,'attack1',True),(0x244,0x28,'attack2',True),(0x26c,0x28,'attack3',True)]
CHAR_RS=418
CHAR_FIELDS=[(0,0x20,'name',False),(0x20,6,'age',False),(0x26,8,'height',False),(0x2e,6,'blood',False),
 (0x34,12,'birthday',False),(0x40,18,'hometown',False),(0x52,16,'weapon',False),(0x62,0x140,'desc',False)]
LOC_RS=32
LOC_FIELDS=[(0,32,'name',False)]
SUM_RS=284
SUM_FIELDS=[(0,0x16,'name',False),(0x16,0x16,'attack',False),(0x2c,0x14,'element',False),
 (0x40,8,'mp',False),(0x48,12,'x',False),(0x54,0xc8,'desc',False)]
NUMERIC={'lv','hp','mp','exp','ap','gil','x'}
NUM_WORDS={'可変':'Varies','即死':'Instakill','10万':'100,000'}
ITEMS={0:(MON_RS,MON_FIELDS,'mon'),1:(CHAR_RS,CHAR_FIELDS,'chr'),2:(LOC_RS,LOC_FIELDS,'loc'),9:(SUM_RS,SUM_FIELDS,'sum')}

# ------------------------------------------------------------------ LZSS
def decompress_file(d):
    items=[]; cur=None
    prev=1
    for b in range(0,len(d),0x400):
        cnt,end,osz=struct.unpack('<IHH',d[b:b+8])
        if end==0: continue
        if prev==1:
            cur=bytearray(); ring=bytearray(N); r=R0
            items.append(dict(off=b,nblocks=cnt,data=cur))
        prev=cnt
        i=b+8; e=b+end
        while i<e:
            fl=d[i]; i+=1
            for k in range(8):
                if i>=e: break
                if fl>>k&1:
                    c=d[i]; i+=1; cur.append(c); ring[r]=c; r=(r+1)%N
                else:
                    lo=d[i]; hi=d[i+1]; i+=2
                    pos=lo|((hi&0xf0)<<4); ln=(hi&15)+THR
                    for _ in range(ln):
                        c=ring[pos%N]; pos+=1; cur.append(c); ring[r]=c; r=(r+1)%N
    return items

def lz_tokens(data):
    """Optimal (min-bits) LZSS parse, window 4096, len 3..18."""
    n=len(data)
    chain={}           # 3-byte key -> ascending list of positions already inserted
    L=[0]*n; D=[0]*n   # longest match length / its distance at each position
    for i in range(n):
        if i+3<=n:
            lst=chain.get(data[i:i+3])
            if lst:
                mx=min(F,n-i); best=0; bd=0; tries=0
                for j in range(len(lst)-1,-1,-1):
                    p=lst[j]; d=i-p
                    if d>N: break
                    l=3
                    while l<mx and data[p+l]==data[i+l]: l+=1
                    if l>best:
                        best=l; bd=d
                        if best==mx: break
                    tries+=1
                    if tries>400: break
                L[i]=best; D[i]=bd
            chain.setdefault(data[i:i+3],[]).append(i)
    INF=10**9
    cost=[0]*(n+1); choice=[0]*(n+1)
    for i in range(n-1,-1,-1):
        c=9+cost[i+1]; ch=1
        if L[i]>=3:
            for l in range(3,L[i]+1):
                cc=17+cost[i+l]
                if cc<c: c=cc; ch=l
        cost[i]=c; choice[i]=ch
    out=[]; i=0
    while i<n:
        ch=choice[i]
        if ch==1: out.append(('L',data[i])); i+=1
        else: out.append(('M',D[i],ch)); i+=ch
    return out

def compress_item(data, cap=None, toks=None):
    toks=toks or lz_tokens(data)
    # raw position of every token for ring pos computation
    blocks=[]; cur=bytearray(); curraw=0; i=0; rawpos=0
    ti=0
    def encode_group(ti,rawpos):
        flags=0; body=bytearray(); used=0; raw=0
        for k in range(8):
            if ti+k>=len(toks): break
            t=toks[ti+k]
            if t[0]=='L': flags|=1<<k; body.append(t[1]); raw+=1
            else:
                _,d,l=t
                pos=(R0+rawpos+raw-d)%N
                body+=bytes([pos&0xff,((pos>>4)&0xf0)|(l-THR)]); raw+=l
            used+=1
        return bytes([flags])+bytes(body),used,raw
    # cap on raw bytes per block so that we can hit nblocks_target exactly
    while ti<len(toks):
        blk=bytearray(); braw=0
        while ti<len(toks):
            g,used,raw=encode_group(ti,rawpos)
            if 8+len(blk)+len(g)>0x400: break
            if cap and braw and braw+raw>cap: break
            blk+=g; braw+=raw; rawpos+=raw; ti+=used
        blocks.append((bytes(blk),braw))
    return blocks

def fit_item(raw,nb,off):
    toks=lz_tokens(raw)
    blocks=compress_item(raw,None,toks)
    if len(blocks)>nb:
        raise SystemExit('item @0x%x needs %d blocks but only %d are available: translation compresses worse than the original '
                         '(shorten some strings)'%(off,len(blocks),nb))
    cap=-(-len(raw)//nb)
    while len(blocks)<nb and cap>64:          # spread over exactly nb blocks so the file layout never changes
        cap-=8
        blocks=compress_item(raw,cap,toks)
    if len(blocks)!=nb: raise SystemExit('could not fit item @0x%x into %d blocks'%(off,nb))
    used=sum(len(b) for b,_ in blocks)
    return blocks,used

def build_file(items_data, orig_layout, verbose=False):
    """items_data: list of raw item bytes; orig_layout: list of (offset, nblocks) to preserve."""
    out=bytearray()
    for raw,(off,nb) in zip(items_data,orig_layout):
        blocks,used=fit_item(raw,nb,off)
        if verbose: print('item @0x%05x: %d blocks, %d/%d payload bytes (%d spare)'%(off,nb,used,nb*1016,nb*1016-used))
        assert off==len(out),(off,len(out))
        for bi,(b,rawn) in enumerate(blocks):
            out+=(struct.pack('<IHH',nb-bi,8+len(b),rawn)+b).ljust(0x400,b'\0')
        out+=b'\0'*((-len(out))%0x800)
    return bytes(out)

# ------------------------------------------------------------------ text helpers
def get(rec,off,size):
    return rec[off:off+size].split(b'\0')[0]
def dec(b): return b.decode('cp932')
def enc(s): return s.encode('cp932')

def iter_fields(items):
    for idx,(RS,FL,tag) in ITEMS.items():
        raw=items[idx]['data']
        for r in range(len(raw)//RS):
            for off,size,name,split in FL:
                yield idx,r,off,size,name,split,get(raw[r*RS:(r+1)*RS],off,size)

# ------------------------------------------------------------------ commands
def cmd_unpack(path,outdir):
    d=open(path,'rb').read()
    items=decompress_file(d)
    os.makedirs(outdir,exist_ok=True)
    for n,it in enumerate(items): open(f'{outdir}/item{n}.bin','wb').write(it['data'])
    layout=[(it['off'],it['nblocks']) for it in items]
    open(f'{outdir}/layout.txt','w').write('\n'.join('%d %d'%x for x in layout))
    # unique strings (atoms for '/'-lists)
    seen={}
    for idx,r,off,size,name,split,b in iter_fields(items):
        if not b or name in('lv','hp','mp','exp','ap','gil','x') : continue
        t=dec(b)
        parts=t.split('/') if split else [t]
        for p in parts:
            if p=='' : continue
            e=seen.setdefault(p,{'cap':size,'ctx':set(),'n':0})
            e['cap']=min(e['cap'],size); e['ctx'].add(ITEMS[idx][2]+'.'+name); e['n']+=1
    with open(f'{outdir}/strings.tsv','w',encoding='utf-8',newline='') as f:
        w=csv.writer(f,delimiter='\t'); w.writerow(['jp','en','where','uses'])
        for p,e in seen.items(): w.writerow([p,'',','.join(sorted(e['ctx'])),e['n']])
    print('items',len(items),'unique strings',len(seen))

def load_tr(path):
    tr={}
    for row in csv.DictReader(open(path,encoding='utf-8'),delimiter='\t'):
        if row['en'].strip(): tr[row['jp']]=row['en']
    return tr

def cmd_repack(srcdir,trfile,outpath,fullwidth=False,upper=False):
    layout=[tuple(map(int,l.split())) for l in open(f'{srcdir}/layout.txt').read().split('\n')]
    raws=[bytearray(open(f'{srcdir}/item{n}.bin','rb').read()) for n in range(len(layout))]
    tr=load_tr(trfile)
    miss=set(); over=[]
    for idx,(RS,FL,tag) in ITEMS.items():
        raw=raws[idx]
        for r in range(len(raw)//RS):
            for off,size,name,split in FL:
                a=r*RS+off
                b=get(raw[a:a+size],0,size)
                if not b: continue
                t=dec(b)
                if name in NUMERIC:                      # numbers: full-width digits -> ASCII, few special words
                    t=NUM_WORDS.get(t,t)
                    t=t.translate({i:i-0xfee0 for i in range(0xff10,0xff1a)}).replace('\u00d7','x')
                    eb=enc(t); raw[a:a+size]=eb.ljust(size,b'\0'); continue
                parts=t.split('/') if split else [t]
                new=[]
                for p in parts:
                    if p in tr: new.append(tr[p])
                    else: new.append(p); miss.add(p)
                s='/'.join(new)
                if upper: s=s.upper()
                if fullwidth: s=s.translate({i:i+0xfee0 for i in range(0x21,0x7f)})
                eb=enc(s)
                if len(eb)>=size: over.append((tag,r,name,len(eb),size,s)); eb=eb[:size-1]
                raw[a:a+size]=eb.ljust(size,b'\0')
    for o in over: print('TOO LONG',o)
    if miss: print('untranslated strings left:',len(miss))
    out=build_file([bytes(x) for x in raws],layout,True)
    open(outpath,'wb').write(out)
    print('wrote',outpath,len(out),'bytes')

if __name__=='__main__':
    c=sys.argv[1]
    if c=='unpack': cmd_unpack(sys.argv[2],sys.argv[3])
    elif c=='repack': cmd_repack(sys.argv[2],sys.argv[3],sys.argv[4],'--fullwidth' in sys.argv,'--upper' in sys.argv)
    elif c=='verify':
        a=decompress_file(open(sys.argv[2],'rb').read()); print([ (hex(i['off']),i['nblocks'],len(i['data'])) for i in a])
