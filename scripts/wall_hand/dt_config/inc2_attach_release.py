"""Inc2: struct-select for AttachSpeed + ReleaseSpeed (the only 2 fully-symmetric V2D fields).
Per field: add BreakVector2D fed by Break_new.<field>; rewire X/Y consumers; delete 2 comp
selects + 2 old BreakVector2D (R/L). Net -3 per field = -6. Compile+validate. No save.
HandOffset/Jog/Run/Sprint SKIPPED (asymmetric R/L handling -> not struct-collapsible).
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
# field -> (break_new out pin, Xconsumer, Yconsumer, Xsel, Ysel, break_R, break_L, newpos)
JOBS={
 'AttachSpeed':('AttachSpeed_16_E648DD8C4B12260DDD6AE1957109E51B',
    ('K2Node_CallFunction_150','B'),('K2Node_CallFunction_152','B'),
    'K2Node_CallFunction_149','K2Node_CallFunction_151','K2Node_CallFunction_146','K2Node_CallFunction_147',[-3480,-1420]),
 'ReleaseSpeed':('ReleaseSpeed_18_880D794B4ABD38C6B57C57B1AE2662E1',
    ('K2Node_CallFunction_157','B'),('K2Node_CallFunction_159','B'),
    'K2Node_CallFunction_156','K2Node_CallFunction_158','K2Node_CallFunction_153','K2Node_CallFunction_154',[-3480,-1240]),
}
def w(m): print(m)
for f,(op,(xcn,xcp),(ycn,ycp),xsel,ysel,bR,bL,pos) in JOBS.items():
    w(f"== {f} ==")
    r=C("add_node",node_type="CallFunction",function_name="BreakVector2D",target_class="KismetMathLibrary",position=pos)
    nv=r.get("id"); w(f"  new BreakVector2D={nv}")
    r=C("connect_pins",source_node=BN,source_pin=op,target_node=nv,target_pin="InVec"); w(f"  Break_new.{f}->InVec: {r.get('success')}")
    r=C("connect_pins",source_node=nv,source_pin="X",target_node=xcn,target_pin=xcp); w(f"  X->{xcn}.{xcp}: {r.get('success')}")
    r=C("connect_pins",source_node=nv,source_pin="Y",target_node=ycn,target_pin=ycp); w(f"  Y->{ycn}.{ycp}: {r.get('success')}")
    for dn,tag in [(xsel,'Xsel'),(ysel,'Ysel'),(bR,'breakR'),(bL,'breakL')]:
        r=C("remove_node",node_id=dn); w(f"  del {tag} {dn}: {r.get('success')}")
w("== compile ==")
r=C("compile_blueprint"); w(f"  compile success={r.get('success')} status={r.get('status')} err={r.get('error_count')} warn={r.get('warning_count')}")
if r.get('errors'): w(f"  ERRORS: {r['errors']}")
r2=C("validate_blueprint")
dis=[x for x in (r2.get('disconnected_nodes') or []) if x.get('graph')=='UpdateWallHandIK']
w(f"  UpdateWallHandIK disconnected: {dis}")
w("DONE (not saved)")
