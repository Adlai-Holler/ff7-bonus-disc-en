# apply jp-keyed json translation files to the tsv
import sys, json
sys.path.insert(0,'/home/claude/scripts'); import exe_tool as t
from safe import sanitize
tsv=sys.argv[1]; T={}
for p in sys.argv[2:]: T.update(json.load(open(p,encoding='utf-8')))
T={k:sanitize(v) for k,v in T.items()}
rows=list(t.read_tsv(tsv)); over=[]
for r in rows:
    r['en']=T.get(r['jp'],'')
    if r['en'] and len(t.encode(r['en']))>int(r['slot']): over.append((r['offset'],r['slot'],len(t.encode(r['en'])),r['en']))
with open(tsv,'w',encoding='utf-8') as f:
    f.write('offset\tjplen\tslot\tjp\ten\tnote\n')
    for r in rows: f.write('\t'.join([r['offset'],r['jplen'],r['slot'],r['jp'],r['en'],''])+'\n')
for o in over: print('OVER',*o)
print(sum(1 for r in rows if r['en']),'of',len(rows),'filled;',len(over),'over')
