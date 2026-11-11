import sys, importlib.util
sys.path.insert(0,'/home/claude/scripts'); import exe_tool as t
uniq=[l.split('\t') for l in open(sys.argv[1],encoding='utf-8').read().split('\n') if l]
T={}
for p in sys.argv[3:]:
    spec=importlib.util.spec_from_file_location('m',p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); T.update(m.T)
from safe import sanitize
byjp={uniq[i][2]:sanitize(en) for i,en in T.items()}
rows=list(t.read_tsv(sys.argv[2])); over=0
for r in rows:
    if r['jp'] in byjp:
        r['en']=byjp[r['jp']]
        if len(t.encode(r['en']))>int(r['slot']): over+=1; print('OVER',r['offset'],r['slot'],len(t.encode(r['en'])),r['en'][:60])
with open(sys.argv[2],'w',encoding='utf-8') as f:
    f.write('offset\tjplen\tslot\tjp\ten\tnote\n')
    for r in rows: f.write('\t'.join([r['offset'],r['jplen'],r['slot'],r['jp'],r['en'],r.get('note','')])+'\n')
print(sum(1 for r in rows if r['en']),'of',len(rows),'rows filled;',over,'over')
