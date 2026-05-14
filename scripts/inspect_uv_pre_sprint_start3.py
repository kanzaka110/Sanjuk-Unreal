import json, re
d = json.load(open('C:/Dev/Sanjuk-Unreal/Saved/Logs/pre_uv_sprint_start.json'))
txt = d['result']['content'][0]['text']
g = json.loads(txt)
nodes = g.get('nodes', [])
print('total nodes:', len(nodes))

# Find ExecutionSequence node(s)
es = [n for n in nodes if 'ExecutionSequence' in n.get('class', '')]
print('\n--- ExecutionSequence nodes ---')
for n in es:
    pins = n.get('pins', [])
    then_pins_info = []
    for p in pins:
        nm = p.get('name', '')
        if nm.startswith('then_'):
            ct = p.get('connected_to', [])
            then_pins_info.append((nm, ct))
    print(f"{n.get('id')} pos={n.get('pos')} total_pins={len(pins)}")
    for nm, ct in then_pins_info:
        print(f"  {nm}: {ct}")

# Find target Sprint End nodes (per memory)
target_ids = ['K2Node_VariableGet_57', 'K2Node_VariableGet_58', 'K2Node_VariableGet_60',
              'K2Node_VariableGet_61', 'K2Node_VariableGet_62', 'K2Node_VariableGet_63',
              'K2Node_VariableGet_64', 'K2Node_VariableGet_65', 'K2Node_VariableGet_66',
              'K2Node_VariableGet_67', 'K2Node_VariableSet_73', 'K2Node_VariableSet_74',
              'K2Node_VariableSet_75', 'K2Node_CallFunction_34', 'K2Node_CallFunction_35',
              'K2Node_CallFunction_36', 'K2Node_CallFunction_37', 'K2Node_CallFunction_38',
              'K2Node_CallFunction_39', 'K2Node_CallFunction_40', 'K2Node_CallFunction_41',
              'K2Node_CallFunction_43', 'K2Node_CallFunction_44', 'K2Node_IfThenElse_0']

print('\n--- Sprint End related node IDs (per memory) ---')
for tid in target_ids:
    match = [n for n in nodes if n.get('id') == tid]
    if match:
        n = match[0]
        title = n.get('title', '')
        print(f"  {tid}  title='{title}'  pos={n.get('pos')}  class={n.get('class')}")
    else:
        print(f"  MISSING: {tid}")

# Max VariableGet/Set/CallFunction IDs used
ids_by_class = {}
for n in nodes:
    nid = n.get('id', '')
    m = re.match(r'^(K2Node_\w+)_(\d+)$', nid)
    if m:
        base = m.group(1)
        idx = int(m.group(2))
        ids_by_class.setdefault(base, []).append(idx)

print('\n--- Max IDs per K2Node class ---')
for k, v in sorted(ids_by_class.items()):
    print(f'{k}: max={max(v)}, count={len(v)}')
