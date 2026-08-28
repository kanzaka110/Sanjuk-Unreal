import json,sys
d=json.load(open('dump_splinepick.json',encoding='utf-8'))
N={n['id']:n for n in d['nodes']}
def title(i): return N[i]['title'].replace('\n',' ')[:46] if i in N else i
def pin(i,name):
    for p in N[i]['pins']:
        if p['name']==name: return p
    return None
def outexec(i,name):
    p=pin(i,name)
    if not p or not p['connected_to']: return None
    return p['connected_to'][0].rsplit('.',1)[0]
# exec chain walk
def walk(start,depth=0,seen=None):
    seen=seen or set()
    cur=start
    while cur and cur not in seen:
        seen.add(cur)
        n=N[cur]
        print('  '*depth+f'{cur} :: {title(cur)}')
        if n['class']=='K2Node_IfThenElse':
            c=pin(cur,'Condition')
            src=c['connected_to'][0] if c['connected_to'] else c.get('default_value')
            print('  '*depth+f'   cond <- {src}')
            for br in ('then','else'):
                nx=outexec(cur,br)
                print('  '*depth+f'   [{br}]')
                if nx: walk(nx,depth+2,seen)
            return
        nx=None
        for pn in ('then','Then','output','execute_out'):
            nx=outexec(cur,pn)
            if nx: break
        cur=nx
entry='K2Node_FunctionEntry_0'
e=outexec(entry,'then')
print('ENTRY ->',e)
walk(e)
