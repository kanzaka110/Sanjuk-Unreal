import json
d = json.load(open('C:/Dev/Sanjuk-Unreal/Saved/Logs/pre_uv_sprint_start.json'))
txt = d['result']['content'][0]['text']
g = json.loads(txt)
nodes = g.get('nodes', [])

# trace from ExecSeq_3.then_12 -> Knot_1 ->? until branching
chain_ids = ['K2Node_Knot_1', 'K2Node_Knot_24', 'K2Node_Knot_0', 'K2Node_Knot_19',
             'K2Node_Knot_13', 'K2Node_Knot_11', 'K2Node_Knot_3', 'K2Node_Knot_8',
             'K2Node_Knot_15', 'K2Node_Knot_82', 'K2Node_IfThenElse_0',
             'K2Node_VariableSet_73', 'K2Node_VariableSet_74', 'K2Node_VariableSet_75']

print('--- Trace exec from candidate Knots ---')
for tid in chain_ids:
    match = [n for n in nodes if n.get('id') == tid]
    if not match:
        print(f'MISSING {tid}')
        continue
    n = match[0]
    print(f"\n{tid}  title='{n.get('title','')}'  pos={n.get('pos')}")
    for p in n.get('pins', []):
        nm = p.get('name')
        d_ = p.get('direction')
        ct = p.get('connected_to', [])
        if d_ == 'output' or nm in ('execute', 'OutputPin', 'then'):
            print(f"  [{d_}] {nm} -> {ct}")
        elif d_ == 'input' and nm in ('execute', 'InputPin'):
            print(f"  [in] {nm} <- ")

# Also IfThenElse_0 input
print('\n--- IfThenElse_0 (Branch end gate) ---')
for n in nodes:
    if n.get('id') == 'K2Node_IfThenElse_0':
        for p in n.get('pins', []):
            print(f"  {p.get('name')} [{p.get('direction')}] -> {p.get('connected_to')}")
