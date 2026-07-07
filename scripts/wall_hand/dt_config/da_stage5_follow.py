"""Stage 5: wire MoveFollow.Pct (Z-bob 0.4) from DA. Clean, behaviorally neutral (0.4==0.4).
Also inspect CF_38 (spine-lean magnitude) to decide SpineLeanMaxDeg wiring.
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

RB="K2Node_BreakStruct_0"
d=C("get_node_details",node_id=RB)
MF=next(p['name'] for p in d['pins'] if p['direction']=='output' and p['name'].split('_')[0]=='MoveFollow')
w(f"RWall.MoveFollow pin = {MF}")

# Break S_WallHandFollow <- RWall.MoveFollow ; .Pct -> CF_100.B
r=C("add_node",node_type="break_struct",struct_type="S_WallHandFollow",position=[-1200,-1300]); BF=r.get("id")
w(f"Break MoveFollow = {BF}")
dd=C("get_node_details",node_id=BF)
inpin=[p['name'] for p in dd['pins'] if p['direction']=='input'][0]
PCT=next(p['name'] for p in dd['pins'] if p['direction']=='output' and p['name'].split('_')[0]=='Pct')
r=C("connect_pins",source_node=RB,source_pin=MF,target_node=BF,target_pin=inpin); w(f"  MoveFollow->break: {r.get('success')} {'' if r.get('success') else r}")
r=C("connect_pins",source_node=BF,source_pin=PCT,target_node="K2Node_CallFunction_100",target_pin="B"); w(f"  Pct->CF_100.B: {r.get('success')} {'' if r.get('success') else r}")

# inspect CF_38 (spine lean magnitude) for later decision
d38=C("get_node_details",node_id="K2Node_CallFunction_38")
w("CF_38 ("+d38.get('function','?')+") inputs:")
for p in d38['pins']:
    if p['direction']=='input':
        w(f"   .{p['name']}: connected={bool(p.get('connected_to'))} default={p.get('default_value')} src={p.get('connected_to')}")

r=C("compile_blueprint"); w(f"[compile] success={r.get('success')} err={r.get('error_count')} warn={r.get('warning_count')}")
if r.get('errors'): w("  ERRORS: "+str(r['errors']))
r2=C("validate_blueprint"); dis=[x for x in (r2.get('disconnected_nodes') or []) if x.get('graph')=='UpdateWallHandIK']
w(f"  disconnected in graph: {len(dis)}")
w("DONE (not saved)")
