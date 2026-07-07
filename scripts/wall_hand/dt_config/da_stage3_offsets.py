"""Stage 3: wire side Jog/Run/Sprint offsets (X via Select_0, Y via Select_2) from DA.
Add BreakVector2D per (wall, field); connect X/Y to the existing bRight R/L selects' A/B.
Behavior change: LEFT X offset sign flips (-5->+5 etc.) per DA.LWall design. Y unchanged.
All additive (connect to A/B pins currently holding literals). Compile+validate. No save.
"""
import json, urllib.request
MCP="http://localhost:9316/mcp"; BP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"; G="UpdateWallHandIK"
def call(a,p):
    b={"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"blueprint_query","arguments":{"action":a,"params":p}}}
    r=urllib.request.Request(MCP,data=json.dumps(b).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=120) as x: raw=json.loads(x.read().decode())
    try:
        if "result" in raw and "content" in raw["result"]:
            t=raw["result"]["content"][0]["text"]; return json.loads(t) if t.strip() else {"success":None,"_raw":t}
    except Exception as e: return {"_err":str(e),"_raw":raw}
    return raw
def C(a,**p): p.update(asset_path=BP,graph_name=G); return call(a,p)
def w(m): print(m)

RB,LB="K2Node_BreakStruct_0","K2Node_BreakStruct_1"  # RWall, LWall breaks
def fields(nid):
    d=C("get_node_details",node_id=nid)
    return {p['name'].split('_')[0]:p['name'] for p in d['pins'] if p['direction']=='output'}
rf, lf = fields(RB), fields(LB)

# (label, source_break, field_short, wireX=(node,pin) or None, wireY=(node,pin) or None, pos)
JOBS=[
 ("RJog",  RB,'JogOffset',    ("K2Node_CallFunction_1","A"),  None,                            [5360,-1700]),
 ("LJog",  LB,'JogOffset',    ("K2Node_CallFunction_1","B"),  None,                            [5360,-1560]),
 ("RRun",  RB,'RunOffset',    ("K2Node_CallFunction_30","A"), ("K2Node_CallFunction_32","A"),  [5360,-1420]),
 ("LRun",  LB,'RunOffset',    ("K2Node_CallFunction_30","B"), ("K2Node_CallFunction_32","B"),  [5360,-1280]),
 ("RSprint",RB,'SprintOffset',("K2Node_CallFunction_64","A"), ("K2Node_CallFunction_31","A"),  [5360,-1140]),
 ("LSprint",LB,'SprintOffset',("K2Node_CallFunction_64","B"), ("K2Node_CallFunction_31","B"),  [5360,-1000]),
]
for lbl,brk,fs,wx,wy,pos in JOBS:
    fmap = rf if brk==RB else lf
    fpin = fmap[fs]
    r=C("add_node",node_type="CallFunction",function_name="BreakVector2D",target_class="KismetMathLibrary",position=pos); bv=r.get("id")
    w(f"[{lbl}] BreakVec2D={bv}")
    r=C("connect_pins",source_node=brk,source_pin=fpin,target_node=bv,target_pin="InVec"); w(f"   {fs}->InVec: {r.get('success')} {'' if r.get('success') else r}")
    if wx:
        r=C("connect_pins",source_node=bv,source_pin="X",target_node=wx[0],target_pin=wx[1]); w(f"   X->{wx[0]}.{wx[1]}: {r.get('success')} {'' if r.get('success') else r}")
    if wy:
        r=C("connect_pins",source_node=bv,source_pin="Y",target_node=wy[0],target_pin=wy[1]); w(f"   Y->{wy[0]}.{wy[1]}: {r.get('success')} {'' if r.get('success') else r}")

r=C("compile_blueprint"); w(f"[compile] success={r.get('success')} err={r.get('error_count')} warn={r.get('warning_count')}")
if r.get('errors'): w("  ERRORS: "+str(r['errors']))
r2=C("validate_blueprint"); dis=[x for x in (r2.get('disconnected_nodes') or []) if x.get('graph')=='UpdateWallHandIK']
w(f"  disconnected in graph: {len(dis)}")
w("DONE (not saved)")
