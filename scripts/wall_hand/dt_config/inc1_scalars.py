"""Inc1: struct-select for 7 scalar SideConfig fields.
Select_1 already exists (RWall=Opt0, LWall=Opt1, bRight=Index) -> SWAP options to
LWall=Opt0, RWall=Opt1 so bool(false=0)->L, bool(true=1)=bRight->R (matches bPickA=A=R).
Then Break_new = Break(Select_1) ; rewire 7 consumers to Break_new.<field> ; delete 7 selects.
Compile + validate. Does NOT save (review first).
"""
import json, urllib.request, sys
MCP="http://localhost:9316/mcp"; BP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"; G="UpdateWallHandIK"
def call(action, params):
    body={"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"blueprint_query","arguments":{"action":action,"params":params}}}
    req=urllib.request.Request(MCP,data=json.dumps(body).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=120) as r: raw=json.loads(r.read().decode())
    if "result" in raw and "content" in raw["result"]: return json.loads(raw["result"]["content"][0]["text"])
    return raw
def C(a,**p): p.update(asset_path=BP,graph_name=G); return call(a,p)

SEL="K2Node_Select_1"
STRUCT="S_WallHandSideConfig"
# field pin names on a break of this struct
FPIN={
 'IKStrength':'IKStrength_2_FBA10DC741495190EA5543A44D2FC94A',
 'SpineLeanMaxDeg':'SpineLeanMaxDeg_22_EB139FAC45752F01A49A8CBAC4E49B2A',
 'ElbowAngleDeg':'ElbowAngleDeg_26_98B6CF29418F5433AA5C0FA7D2025DB6',
 'AttachStartDist':'AttachStartDist_4_B34605FB4CE337463536AAA80512CFF4',
 'AttachFullDist':'AttachFullDist_6_34778D0B45A06E794AA04BAE57609F71',
 'TurnReleaseSpeed':'TurnReleaseSpeed_20_473EA2B4414B56E302170A8AEF6038E8',
 'TurnBlockHold':'TurnBlockHold_24_B129225B4127BFC15DAE698F3832C256',
}
# field -> (old select id, consumer node, consumer pin)
WIRE={
 'IKStrength':('K2Node_CallFunction_130','K2Node_CallFunction_131','B'),
 'SpineLeanMaxDeg':('K2Node_CallFunction_142','K2Node_CallFunction_143','B'),
 'ElbowAngleDeg':('K2Node_CallFunction_144','K2Node_CallFunction_145','B'),
 'AttachStartDist':('K2Node_CallFunction_132','K2Node_CallFunction_133','B'),
 'AttachFullDist':('K2Node_CallFunction_134','K2Node_CallFunction_135','B'),
 'TurnReleaseSpeed':('K2Node_CallFunction_138','K2Node_CallFunction_139','B'),
 'TurnBlockHold':('K2Node_CallFunction_140','K2Node_CallFunction_141','B'),
}

def w(m): print(m)

# --- 1. swap Select_1 options: LWall->Option0, RWall->Option1 ---
w("[1] swap Select_1 options")
r=C("connect_pins",source_node="K2Node_CallFunction_137",source_pin="LWall",target_node=SEL,target_pin="Option 0")
w(f"   LWall->Opt0: {r.get('success')}")
r=C("connect_pins",source_node="K2Node_CallFunction_137",source_pin="RWall",target_node=SEL,target_pin="Option 1")
w(f"   RWall->Opt1: {r.get('success')}")

# --- 2. add Break_new, connect Select_1.ReturnValue -> break input ---
w("[2] add Break_new")
r=C("add_node",node_type="break_struct",struct_type=STRUCT,position=[-3760,-1650])
BN=r.get("id"); w(f"   Break_new id={BN}")
# find its struct input pin name
det=C("get_node_details",node_id=BN)
inpin=[p['name'] for p in det['pins'] if p['direction']=='input'][0]
w(f"   break input pin={inpin}")
r=C("connect_pins",source_node=SEL,source_pin="ReturnValue",target_node=BN,target_pin=inpin)
w(f"   Select->Break: {r.get('success')}")
# verify break output field pins match FPIN
outpins={p['name'].split('_')[0]:p['name'] for p in det['pins'] if p['direction']=='output'}

# --- 3. rewire 7 consumers to Break_new.field ---
w("[3] rewire consumers")
for f,(oldsel,cn,cp) in WIRE.items():
    fp=outpins.get(f, FPIN[f])
    r=C("connect_pins",source_node=BN,source_pin=fp,target_node=cn,target_pin=cp)
    w(f"   {f:16s} Break_new.{f} -> {cn}.{cp}: {r.get('success')}")

# --- 4. delete 7 old scalar selects ---
w("[4] delete old selects")
for f,(oldsel,cn,cp) in WIRE.items():
    r=C("remove_node",node_id=oldsel)
    w(f"   remove {oldsel} ({f}): {r.get('success')}")

# --- 5. compile + validate ---
w("[5] compile")
r=C("compile_blueprint")
w(f"   compile: success={r.get('success')} status={r.get('status')} errors={r.get('error_count')} warnings={r.get('warning_count')}")
if r.get('errors'): w(f"   ERRORS: {r['errors']}")
r2=C("validate_blueprint")
w(f"   validate: disconnected={r2.get('disconnected_nodes')} msgs={r2.get('messages') or r2.get('compiler_messages')}")
w("DONE (not saved)")
