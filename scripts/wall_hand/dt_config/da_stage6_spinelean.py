"""Stage 6: SpineLeanMaxDeg reconstruction. Current InSpineLean = sign*|dot|*ramp in [-1,1]
(normalized factor). DA SpineLeanMaxDeg=28.6 = degrees scale. Insert *SpineLeanMaxDeg to
convert to degrees. Behavior CHANGES (lean scales up) -> PIE verify. Revert = remove Mul.
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
SLM=next(p['name'] for p in d['pins'] if p['direction']=='output' and p['name'].split('_')[0]=='SpineLeanMaxDeg')
w(f"RWall.SpineLeanMaxDeg pin = {SLM}")

# insert: CF_15 * SpineLeanMaxDeg -> InSpineLean
r=C("disconnect_pins",node_id="K2Node_CallFunction_20",pin_name="InSpineLean"); w(f"disconnect InSpineLean: {r.get('success')}")
r=C("add_node",node_type="CallFunction",function_name="Multiply_DoubleDouble",target_class="KismetMathLibrary",position=[3760,120]); MUL=r.get("id"); w(f"Mul={MUL}")
r=C("connect_pins",source_node="K2Node_CallFunction_15",source_pin="ReturnValue",target_node=MUL,target_pin="A"); w(f"  CF_15->Mul.A: {r.get('success')} {'' if r.get('success') else r}")
r=C("connect_pins",source_node=RB,source_pin=SLM,target_node=MUL,target_pin="B"); w(f"  SpineLeanMaxDeg->Mul.B: {r.get('success')} {'' if r.get('success') else r}")
r=C("connect_pins",source_node=MUL,source_pin="ReturnValue",target_node="K2Node_CallFunction_20",target_pin="InSpineLean"); w(f"  Mul->InSpineLean: {r.get('success')} {'' if r.get('success') else r}")

r=C("compile_blueprint"); w(f"[compile] success={r.get('success')} err={r.get('error_count')} warn={r.get('warning_count')}")
if r.get('errors'): w("  ERRORS: "+str(r['errors']))
r2=C("validate_blueprint"); dis=[x for x in (r2.get('disconnected_nodes') or []) if x.get('graph')=='UpdateWallHandIK']
w(f"  disconnected in graph: {len(dis)}")
w("DONE (not saved)")
