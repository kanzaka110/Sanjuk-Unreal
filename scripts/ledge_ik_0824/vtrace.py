import json,sys
d=json.load(open('dump_Ledge_HandTarget.json',encoding='utf-8'))
N={n['id']:n for n in d['nodes']}
def T(i): return N[i]['title'].replace('\n',' ')[:44] if i in N else '?'
def src(i,pname):
    for p in N[i]['pins']:
        if p['name']==pname and p['direction']=='input':
            if p['connected_to']: return p['connected_to'][0]
            return 'DEF='+str(p.get('default_value'))
    return None
def expand(ref,depth=0,seen=None,maxd=9):
    seen=seen or set()
    if depth>maxd: print('  '*depth+'...'); return
    if ref is None: print('  '*depth+'<none>'); return
    if isinstance(ref,str) and ref.startswith('DEF='):
        print('  '*depth+ref); return
    nid=ref.rsplit('.',1)[0]; pn=ref.rsplit('.',1)[1]
    if nid not in N: print('  '*depth+ref); return
    n=N[nid]
    print('  '*depth+f'{T(nid)}  ({nid}.{pn})')
    if n['class']=='K2Node_Knot':
        expand(src(nid,'InputPin'),depth,seen,maxd); return
    if nid in seen: print('  '*(depth+1)+'^dup'); return
    seen.add(nid)
    for p in n['pins']:
        if p['direction']=='input' and p['type']!='exec':
            v=p['connected_to'][0] if p['connected_to'] else 'DEF='+str(p.get('default_value'))
            print('  '*(depth+1)+f'.{p["name"]}:')
            expand(v,depth+2,seen,maxd)
tgt=sys.argv[1]; pn=sys.argv[2] if len(sys.argv)>2 else None
if pn: expand(tgt+'.'+pn)
else:
    for p in N[tgt]['pins']:
        if p['direction']=='input' and p['type']!='exec':
            print(f'--- .{p["name"]}')
            expand(p['connected_to'][0] if p['connected_to'] else 'DEF='+str(p.get('default_value')),1)
