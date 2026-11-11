import sys, re
# find runs of valid Shift-JIS double-byte chars (kana/kanji) >= N chars
def scan(data, minchars=4):
    out=[]; i=0; n=len(data)
    while i<n-1:
        j=i; cnt=0
        while j<n-1:
            b=data[j]
            if (0x81<=b<=0x9f or 0xe0<=b<=0xef) and (0x40<=data[j+1]<=0xfc and data[j+1]!=0x7f):
                j+=2; cnt+=1
            elif 0x20<=b<0x7f and cnt>0:
                j+=1
            else: break
        if cnt>=minchars:
            try: out.append((i,data[i:j].decode('cp932')))
            except: pass
            i=j
        else: i+=1
    return out
for f in sys.argv[1:]:
    d=open(f,'rb').read(); r=scan(d)
    print(f"== {f}: {len(r)} strings")
    for o,s in r[:8]: print(f"  {o:#08x} {s[:60]}")
