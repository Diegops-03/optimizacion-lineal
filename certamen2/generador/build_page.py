import json, os
days=json.load(open('days.json'))
os.makedirs('pub', exist_ok=True)
idx=[]
for d in days:
    meta={k:d[k] for k in ('n','date','block','blockName','title','dayInBlock','blockLen')}
    meta['nEj']=len(d['ejercicios'])
    idx.append(meta)
    json.dump({'clase':d['clase'],'ejemplos':d['ejemplos'],'ejercicios':d['ejercicios']}, open(f"pub/d{d['n']}.json",'w'), ensure_ascii=False)
t=open('template.html').read().replace('__DATA__', json.dumps(idx, ensure_ascii=False).replace('</','<\\/'))
open('ruta_c2.html','w').write(t)
print(len(t), sum(os.path.getsize(f'pub/d{i}.json') for i in range(1,28)))
