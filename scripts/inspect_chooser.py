import unreal, json

asset_path = '/Game/Art/Character/PC/PC_01/StateMachine/GroundMoving'
ct = unreal.load_asset(asset_path)
print('class:', ct.get_class().get_name())

# Try all relevant property accessors
out = {'asset': asset_path, 'class': ct.get_class().get_name()}

# Probe properties (different UE versions name differently)
candidates = [
    'columns_structs', 'columns', 'cost_columns_structs',
    'results_structs', 'results',
    'output_object_type', 'context_object_type',
    'next_chooser', 'fallback_result',
    'output_struct_type'
]
for name in candidates:
    try:
        v = ct.get_editor_property(name)
        out[name] = repr(v)[:500]
    except Exception as e:
        out[name + '_err'] = str(e)[:200]

# Also list editor properties available
try:
    props = []
    for p in dir(ct):
        if not p.startswith('_') and p not in ('get_editor_property','set_editor_property','get_class'):
            props.append(p)
    out['dir_sample'] = props[:80]
except Exception as e:
    out['dir_err'] = str(e)

print(json.dumps(out, ensure_ascii=False, indent=2)[:6000])
