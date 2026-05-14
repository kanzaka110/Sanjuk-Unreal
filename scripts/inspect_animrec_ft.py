import json
d=json.load(open('C:/Dev/Sanjuk-Unreal/Saved/Logs/animrec_pre.json'))
g=json.loads(d['result']['content'][0]['text'])
nodes=g.get('nodes',[])

# Track FT_5 -> FT_8 -> ... order via exec/data chain
for n in nodes:
    if 'FormatText' not in n.get('class',''):
        continue
    print(f"\n=== {n.get('id')}  pos={n.get('pos')} ===")
    for p in n.get('pins',[]):
        nm=p.get('name')
        d_=p.get('direction')
        ct=p.get('connected_to',[])
        dv=p.get('default_value','')
        if dv and len(dv)>80:
            dv=dv[:80]+'...'
        print(f"  [{d_}] {nm} type={p.get('type')} default={repr(dv)} -> {ct}")
