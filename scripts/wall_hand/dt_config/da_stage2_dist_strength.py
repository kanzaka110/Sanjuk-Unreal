"""Stage 2: wire AttachStartDist/FullDist + IKStrength (side) from DA. Behaviorally neutral
(DA values == current literals: 60/45/1). Additive except 1 data-wire insert for IKStrength mul.
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

RB="K2Node_BreakStruct_0"  # RWall break
# resolve RWall field pin names
det=C("get_node_details",node_id=RB)
fp={p['name'].split('_')[0]:p['name'] for p in det['pins'] if p['direction']=='output'}
w("RWall break fields: "+str(list(fp.keys())))
ASD, AFD, IKS = fp['AttachStartDist'], fp['AttachFullDist'], fp['IKStrength']

# 1. attach distances -> CF_21 InRangeA/B (replaces literals 60/45)
r=C("connect_pins",source_node=RB,source_pin=ASD,target_node="K2Node_CallFunction_21",target_pin="InRangeA"); w(f"[1a] AttachStartDist->CF_21.InRangeA: {r.get('success')} {'' if r.get('success') else r}")
r=C("connect_pins",source_node=RB,source_pin=AFD,target_node="K2Node_CallFunction_21",target_pin="InRangeB"); w(f"[1b] AttachFullDist->CF_21.InRangeB: {r.get('success')} {'' if r.get('success') else r}")

# 2. IKStrength mul insertion: CF_21 -> [Mul(*IKStrength)] -> Knot_69 -> InAlphaTarget
r=C("add_node",node_type="CallFunction",function_name="Multiply_DoubleDouble",target_class="KismetMathLibrary",position=[3040,-140]); MUL=r.get("id")
w(f"[2] add Mul -> {MUL} {'' if MUL else r}")
r=C("disconnect_pins",node_id="K2Node_Knot_69",pin_name="InputPin"); w(f"[2a] disconnect Knot_69.InputPin: {r.get('success')}")
r=C("connect_pins",source_node="K2Node_CallFunction_21",source_pin="ReturnValue",target_node=MUL,target_pin="A"); w(f"[2b] CF_21->Mul.A: {r.get('success')} {'' if r.get('success') else r}")
r=C("connect_pins",source_node=RB,source_pin=IKS,target_node=MUL,target_pin="B"); w(f"[2c] IKStrength->Mul.B: {r.get('success')} {'' if r.get('success') else r}")
r=C("connect_pins",source_node=MUL,source_pin="ReturnValue",target_node="K2Node_Knot_69",target_pin="InputPin"); w(f"[2d] Mul->Knot_69: {r.get('success')} {'' if r.get('success') else r}")

# 3. verify
r=C("compile_blueprint"); w(f"[3] compile success={r.get('success')} err={r.get('error_count')} warn={r.get('warning_count')}")
if r.get('errors'): w("  ERRORS: "+str(r['errors']))
r2=C("validate_blueprint"); dis=[x for x in (r2.get('disconnected_nodes') or []) if x.get('graph')=='UpdateWallHandIK']
w(f"  disconnected in graph: {len(dis)}")
w(f"STAGE2 IDS: Mul={MUL}")
w("DONE (not saved)")
