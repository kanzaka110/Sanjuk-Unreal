"""Inc3: struct-select for IdleFollow + MoveFollow (both symmetric R/L on bRight).
Per follow: add Break(S_WallHandFollow) fed by Break_new.<field>; rewire Bone/Pct consumers;
delete 2 selects (Bone SelectName + Pct SelectFloat) + 2 old BreakFollow (R/L). Net -3 each = -6.
"""
import json, urllib.request
MCP="http://localhost:9316/mcp"; BP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"; G="UpdateWallHandIK"
def call(a,p):
    b={"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"blueprint_query","arguments":{"action":a,"params":p}}}
    r=urllib.request.Request(MCP,data=json.dumps(b).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=120) as x: raw=json.loads(x.read().decode())
    if "result" in raw and "content" in raw["result"]: return json.loads(raw["result"]["content"][0]["text"])
    return raw
def C(a,**p): p.update(asset_path=BP,graph_name=G); return call(a,p)

BN="K2Node_BreakStruct_0"
BONE="Bone_2_AAACC57540E103273985A4B46A803401"
PCT="Pct_4_4198ACCE44002F55C2DDCBA9060D05AB"
# name -> (break_new outpin, BoneConsumer, PctConsumer, boneSel, pctSel, breakR, breakL, pos)
JOBS={
 'Idle':('IdleFollow_28_7AB25E91493E156E53E5019D2B4E2CFC',
    ('K2Node_CallFunction_165','B'),('K2Node_CallFunction_161','B'),
    'K2Node_CallFunction_164','K2Node_CallFunction_160','K2Node_BreakStruct_8','K2Node_BreakStruct_10',[-3480,-1060]),
 'Move':('MoveFollow_30_B80DC79C4A8CF8A866EBD2810E5E298A',
    ('K2Node_CallFunction_167','B'),('K2Node_CallFunction_163','B'),
    'K2Node_CallFunction_166','K2Node_CallFunction_162','K2Node_BreakStruct_9','K2Node_BreakStruct_11',[-3480,-880]),
}
def w(m): print(m)
for f,(op,(bcn,bcp),(pcn,pcp),bsel,psel,bR,bL,pos) in JOBS.items():
    w(f"== {f}Follow ==")
    r=C("add_node",node_type="break_struct",struct_type="S_WallHandFollow",position=pos)
    nv=r.get("id"); w(f"  new BreakFollow={nv}")
    det=C("get_node_details",node_id=nv)
    inpin=[p['name'] for p in det['pins'] if p['direction']=='input'][0]
    r=C("connect_pins",source_node=BN,source_pin=op,target_node=nv,target_pin=inpin); w(f"  Break_new.{f}Follow->{inpin}: {r.get('success')}")
    r=C("connect_pins",source_node=nv,source_pin=BONE,target_node=bcn,target_pin=bcp); w(f"  Bone->{bcn}.{bcp}: {r.get('success')}")
    r=C("connect_pins",source_node=nv,source_pin=PCT,target_node=pcn,target_pin=pcp); w(f"  Pct->{pcn}.{pcp}: {r.get('success')}")
    for dn,tag in [(bsel,'boneSel'),(psel,'pctSel'),(bR,'breakR'),(bL,'breakL')]:
        r=C("remove_node",node_id=dn); w(f"  del {tag} {dn}: {r.get('success')}")
w("== compile ==")
r=C("compile_blueprint"); w(f"  compile success={r.get('success')} status={r.get('status')} err={r.get('error_count')} warn={r.get('warning_count')}")
if r.get('errors'): w(f"  ERRORS: {r['errors']}")
r2=C("validate_blueprint")
dis=[x for x in (r2.get('disconnected_nodes') or []) if x.get('graph')=='UpdateWallHandIK']
w(f"  UpdateWallHandIK disconnected: {dis}")
w("DONE (not saved)")
