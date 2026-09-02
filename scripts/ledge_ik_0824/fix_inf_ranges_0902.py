# -*- coding: utf-8 -*-
"""inf 로 저장된 FloatRange 를 FLT_MAX 로 복구 (9/2)"""
import json, re, urllib.request
URL='http://127.0.0.1:9316/mcp'
FLT = 3.402823466e38

def raw(tool, action, params, timeout=300):
    body={"jsonrpc":"2.0","method":"tools/call","id":1,
          "params":{"name":tool,"arguments":{"action":action,"params":params}}}
    req=urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type":"application/json"})
    r=json.load(urllib.request.urlopen(req, timeout=timeout))
    txt=r["result"]["content"][0]["text"]
    if r["result"].get("isError"): raise RuntimeError(action+": "+txt[:400])
    return txt

def call(tool, action, params):
    txt = raw(tool, action, params)
    # 비표준 토큰 정리 (inf / -inf / nan)
    txt2 = re.sub(r'(?<![\w"])-?inf(?![\w"])', '1e39', txt)
    txt2 = re.sub(r'(?<![\w"])-?nan(?![\w"])', '0', txt2)
    try:
        return json.loads(txt2)
    except Exception:
        return json.loads(txt2.replace('Infinity','1e39').replace('NaN','0'))

C='/Game/Art/Character/PC/PC_01/StateMachine/CustomMove/LedgeAll_Test'
ch=lambda a,p: call('chooser_query', a, p)
v=ch('inspect_chooser', {'asset_path':C,'include_cells':True})
cells={c['index']:{x['row']:x for x in (c.get('cells') or [])} for c in v['columns']}
print('행', v['row_count'], flush=True)
fixed=0
for col in (2,3,4):
    for r in range(v['row_count']):
        c=cells.get(col,{}).get(r)
        if not c or 'min' not in c: continue
        lo,hi=c['min'],c['max']
        nlo = -FLT if (lo is None or lo <= -1e38) else lo
        nhi =  FLT if (hi is None or hi >=  1e38) else hi
        if nlo!=lo or nhi!=hi:
            ch('set_chooser_cell', {'asset_path':C,'column_index':col,'row_index':r,
                                    'float_min':nlo,'float_max':nhi})
            fixed+=1
print('복구한 셀', fixed, flush=True)
# 검증: 다시 읽어 inf 잔존 확인
txt = raw('chooser_query','inspect_chooser',{'asset_path':C,'include_cells':True})
print('응답에 inf 잔존:', 'inf' in txt.lower(), flush=True)
