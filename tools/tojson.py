import sys,json,importlib.util
todo=[l.split('\t') for l in open(sys.argv[1],encoding='utf-8').read().split('\n') if l]
spec=importlib.util.spec_from_file_location('m',sys.argv[2]); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
json.dump({todo[i][2]:v for i,v in m.T.items()},open(sys.argv[3],'w',encoding='utf-8'),ensure_ascii=False,indent=0)
print(len(m.T),'entries')
