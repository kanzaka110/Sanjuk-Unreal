"""Inspect AnimRewindRecorderEmit current node list."""
import json
def load_inner(path):
    with open(path,'r',encoding='utf-8') as f:
        d=json.load(f)
    return json.loads(d['result']['content'][0]['text'])

ar = load_inner('Saved/anim_rec_emit_bp.json')
print('nodes:', len(ar['nodes']))
for n in ar['nodes']:
    cls=n['class']; nid=n['id']; title=n.get('title','')
    extra=''
    if cls=='K2Node_FormatText':
        # show format text default value (often in pin named like 'Format' or first input string default)
        fmt_pin=None
        for p in n.get('pins',[]):
            if p['direction']=='input' and isinstance(p.get('default_value'),str) and '{' in p.get('default_value',''):
                fmt_pin=p
                break
        if fmt_pin:
            extra=' fmt='+repr(fmt_pin.get('default_value'))[:200]
    elif cls=='K2Node_VariableGet':
        for p in n.get('pins',[]):
            if p['direction']=='output':
                extra=' var='+p.get('name','?')
                break
    elif cls=='K2Node_CallFunction':
        extra=' fn='+n.get('function','?')
    print(f"  {nid:35s} {cls:30s} title={title[:60]!r}{extra}")
