"""Stage 4: wire FWall.HandOffset -> front forward(X) + hand width(+/-Y).
FWall.HandOffset.X -> CF_26.B (forward mult). .Y -> CF_41.Z (+width), .Y*-1 -> CF_34.Z (-width).
Behaviorally neutral (DA HandOffset=(12.4,12.4) == current literals). Additive + 1 negate node.
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

FB="K2Node_BreakStruct_2"  # FWall break
d=C("get_node_details",node_id=FB)
HO=next(p['name'] for p in d['pins'] if p['direction']=='output' and p['name'].split('_')[0]=='HandOffset')
w(f"FWall.HandOffset pin = {HO}")

# BreakVector2D for FWall.HandOffset
r=C("add_node",node_type="CallFunction",function_name="BreakVector2D",target_class="KismetMathLibrary",position=[-1200,-1600]); BV=r.get("id")
w(f"BreakVec2D(FWall.HandOffset) = {BV}")
r=C("connect_pins",source_node=FB,source_pin=HO,target_node=BV,target_pin="InVec"); w(f"  HandOffset->InVec: {r.get('success')} {'' if r.get('success') else r}")
# X -> forward (CF_26.B)
r=C("connect_pins",source_node=BV,source_pin="X",target_node="K2Node_CallFunction_26",target_pin="B"); w(f"  X->CF_26.B(forward): {r.get('success')} {'' if r.get('success') else r}")
# Y -> +width (CF_41.Z)
r=C("connect_pins",source_node=BV,source_pin="Y",target_node="K2Node_CallFunction_41",target_pin="Z"); w(f"  Y->CF_41.Z(+width): {r.get('success')} {'' if r.get('success') else r}")
# Y * -1 -> -width (CF_34.Z)
r=C("add_node",node_type="CallFunction",function_name="Multiply_DoubleDouble",target_class="KismetMathLibrary",position=[-900,-1500]); NEG=r.get("id")
w(f"Negate mul = {NEG}")
r=C("connect_pins",source_node=BV,source_pin="Y",target_node=NEG,target_pin="A"); w(f"  Y->Neg.A: {r.get('success')} {'' if r.get('success') else r}")
r=C("set_pin_default",node_id=NEG,pin_name="B",value="-1.0"); w(f"  Neg.B=-1: {r.get('success')}")
r=C("connect_pins",source_node=NEG,source_pin="ReturnValue",target_node="K2Node_CallFunction_34",target_pin="Z"); w(f"  Neg->CF_34.Z(-width): {r.get('success')} {'' if r.get('success') else r}")

r=C("compile_blueprint"); w(f"[compile] success={r.get('success')} err={r.get('error_count')} warn={r.get('warning_count')}")
if r.get('errors'): w("  ERRORS: "+str(r['errors']))
r2=C("validate_blueprint"); dis=[x for x in (r2.get('disconnected_nodes') or []) if x.get('graph')=='UpdateWallHandIK']
w(f"  disconnected in graph: {len(dis)}")
w("DONE (not saved)")
