"""Dump all FormatText nodes' raw structure with ALL pins."""
import json
def load_inner(path):
    with open(path,'r',encoding='utf-8') as f:
        d=json.load(f)
    return json.loads(d['result']['content'][0]['text'])

dd = load_inner('Saved/drawdebug_bp.json')

for n in dd['nodes']:
    if n['class']!='K2Node_FormatText': continue
    print(f"\n=== {n['id']} ===")
    print(json.dumps({k:v for k,v in n.items() if k!='pins'}, indent=2, ensure_ascii=False))
    for p in n.get('pins',[]):
        marker = '*' if 'Format' in p['name'] or '{' in str(p.get('default_value','')) else ' '
        print(f"  {marker} dir={p['direction']:6s} name={p['name']:25s} type={p.get('type'):15s} default={p.get('default_value')!r}")
