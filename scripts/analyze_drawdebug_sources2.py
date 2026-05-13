"""Phase 2: trace EnumeratorNameAsString back to their byte/enum source, PropertyAccess details, and CallFunction signatures."""
import json
from collections import defaultdict

def load_inner(path):
    with open(path, 'r', encoding='utf-8') as f:
        d = json.load(f)
    txt = d['result']['content'][0]['text']
    return json.loads(txt)

dd = load_inner('Saved/drawdebug_bp.json')

def index_nodes(g):
    by_id = {n['id']: n for n in g['nodes']}
    pin_index = {}
    for n in g['nodes']:
        for p in n.get('pins', []):
            pin_index[p['id']] = (n['id'], p)
    return by_id, pin_index

dd_nodes, dd_pins = index_nodes(dd)

def get_pin(node, name, direction=None):
    for p in node.get('pins', []):
        if p['name'] == name and (direction is None or p['direction'] == direction):
            return p
    return None

def trace_input(pin):
    out=[]
    for ref in (pin.get('connected_to') or []):
        if '.' in ref:
            nid, pname = ref.split('.',1)
        else:
            nid, pname = ref, None
        out.append((nid,pname))
    return out

def node_summary(nid):
    n=dd_nodes.get(nid)
    if not n: return f"<MISSING:{nid}>"
    extra=''
    for p in n.get('pins',[]):
        if p['direction']=='input' and p.get('default_value') is not None and not p.get('connected_to'):
            extra += f" {p['name']}={p['default_value']!r}"
    return f"{nid} [{n['class']}] title={n.get('title','')[:60]!r}{extra}"

# 1) Trace every K2Node_GetEnumeratorNameAsString
print('==== EnumeratorNameAsString sources ====')
for n in dd['nodes']:
    if n['class'] != 'K2Node_GetEnumeratorNameAsString':
        continue
    # input pin is usually 'Enumerator'
    in_pin = None
    for p in n.get('pins',[]):
        if p['direction']=='input' and p['name'] != 'self' and p['name'] != 'execute':
            in_pin = p
            break
    print(f"\n  {n['id']}:")
    print(f"    enum_type={in_pin.get('type') if in_pin else '?'}")
    if in_pin:
        srcs = trace_input(in_pin)
        for nid, pname in srcs:
            print(f"    <- {node_summary(nid)} :: pin={pname}")
        if not srcs:
            print(f"    default={in_pin.get('default_value')!r}")

# 2) PropertyAccess_0 details
print('\n==== PropertyAccess_0 details ====')
pa = dd_nodes.get('K2Node_PropertyAccess_0')
if pa:
    print('  class:', pa['class'])
    print('  title:', pa.get('title'))
    for k,v in pa.items():
        if k not in ('id','class','title','pins'):
            print(f"  {k}: {v}")
    for p in pa.get('pins',[]):
        print(f"    pin: dir={p['direction']:6s} name={p['name']:20s} type={p.get('type')} default={p.get('default_value')!r}")
        if p.get('connected_to'):
            print(f"        connected_to={p.get('connected_to')}")

# 3) CallFunction_43 detail (struct break)
print('\n==== CallFunction_43 (TravelActionResult) ====')
cf=dd_nodes.get('K2Node_CallFunction_43')
if cf:
    print('  title:', cf.get('title'))
    for k,v in cf.items():
        if k not in ('id','class','title','pins'):
            print(f"  {k}: {v}")
    for p in cf.get('pins',[]):
        print(f"    {p['direction']:6s} {p['name']:35s} type={p.get('type')} default={p.get('default_value')!r}")

# 4) CallFunction_119, _120, _121, _118
print('\n==== CallFunction_118/119/120/121 detail ====')
for nid in ['K2Node_CallFunction_118','K2Node_CallFunction_119','K2Node_CallFunction_120','K2Node_CallFunction_121']:
    n=dd_nodes.get(nid)
    if not n:
        print(f"  {nid}: <MISSING>"); continue
    print(f"\n  {nid}: title={n.get('title')}")
    for k,v in n.items():
        if k not in ('id','class','title','pins'):
            print(f"    {k}: {v}")
    for p in n.get('pins',[]):
        if p['direction']=='input' and p['name'] not in ('self','execute'):
            srcs = trace_input(p)
            print(f"    IN  {p['name']:20s} type={p.get('type')} default={p.get('default_value')!r}")
            for sid, sname in srcs:
                print(f"        <- {node_summary(sid)} :: pin={sname}")

# 5) Track VariableGet nodes referenced and check vars
print('\n==== VariableGet nodes (drawdebug) ====')
vget_uses = []
for n in dd['nodes']:
    if n['class']!='K2Node_VariableGet': continue
    # output pin's name is the var name
    out_pin = next((p for p in n.get('pins',[]) if p['direction']=='output'), None)
    var_name = out_pin['name'] if out_pin else '???'
    title = n.get('title','')
    vget_uses.append((n['id'], var_name, title))

# Print specifically VariableGet_30 (UBSW)
print('\n  Focus: K2Node_VariableGet_30')
n=dd_nodes.get('K2Node_VariableGet_30')
if n:
    for k,v in n.items():
        if k!='pins':
            print(f"    {k}: {v}")
    for p in n.get('pins',[]):
        print(f"    pin: dir={p['direction']:6s} name={p['name']:30s} type={p.get('type')} default={p.get('default_value')!r}")

print('\n  Focus: K2Node_VariableGet_12, _13')
for nid in ['K2Node_VariableGet_12','K2Node_VariableGet_13']:
    n=dd_nodes.get(nid)
    print(f"\n    {nid}:")
    if not n:
        print('      <MISSING>'); continue
    for k,v in n.items():
        if k!='pins':
            print(f"      {k}: {v}")
    for p in n.get('pins',[]):
        print(f"      pin: dir={p['direction']:6s} name={p['name']:30s} type={p.get('type')} default={p.get('default_value')!r}")
