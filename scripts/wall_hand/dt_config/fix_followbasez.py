"""Restore WHFollowBaseZ baseline capture (lost in revert) so follow = DELTA not absolute.
- Get WHFollowBaseZ -> FInterpTo(Current=WHFollowBaseZ, Target=CF_98 pelvisRelZ, dt=0.0167, spd=2.0) -> Set WHFollowBaseZ (exec insert after GetConfig CF_55)
- CF_99.B <- WHFollowBaseZ  (so CF_99 = CF_98 - WHFollowBaseZ = delta, ~0 at rest)
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
def conn(sn,sp,tn,tp,tag):
    r=C("connect_pins",source_node=sn,source_pin=sp,target_node=tn,target_pin=tp); w(f"   {tag}: {r.get('success')}"+("" if r.get('success') else f" {r}"))

# 1. VariableGet WHFollowBaseZ
get1=C("add_node",node_type="VariableGet",variable_name="WHFollowBaseZ",position=[400,220]).get("id"); w(f"get={get1}")
# 2. FInterpTo
fi=C("add_node",node_type="CallFunction",function_name="FInterpTo",target_class="KismetMathLibrary",position=[650,150]).get("id"); w(f"FInterp={fi}")
d=C("get_node_details",node_id=fi); w("  FInterp pins: "+str([p['name'] for p in d['pins']]))
conn(get1,"WHFollowBaseZ",fi,"Current","get->FI.Current")
conn("K2Node_CallFunction_98","ReturnValue",fi,"Target","CF_98->FI.Target")
C("set_pin_default",node_id=fi,pin_name="DeltaTime",value="0.016667")
C("set_pin_default",node_id=fi,pin_name="InterpSpeed",value="2.0")
# 3. VariableSet WHFollowBaseZ <- FInterp
set1=C("add_node",node_type="VariableSet",variable_name="WHFollowBaseZ",position=[900,150]).get("id"); w(f"set={set1}")
conn(fi,"ReturnValue",set1,"WHFollowBaseZ","FI->set.value")
# 4. exec insert: CF_55.then -> set1 -> VariableSet_0
C("disconnect_pins",node_id="K2Node_VariableSet_0",pin_name="execute")
conn("K2Node_CallFunction_55","then",set1,"execute","CF_55.then->set.exec")
conn(set1,"then","K2Node_VariableSet_0","execute","set.then->SetSmoothVel")
# 5. CF_99.B <- WHFollowBaseZ (delta)
conn(get1,"WHFollowBaseZ","K2Node_CallFunction_99","B","get->CF_99.B(delta)")

r=C("compile_blueprint"); w(f"[compile] success={r.get('success')} err={r.get('error_count')}")
if r.get('errors'): w("  ERR:"+str(r['errors']))
r2=C("validate_blueprint"); dis=[x for x in (r2.get('disconnected_nodes') or []) if x.get('graph')=='UpdateWallHandIK']
w(f"  disconnected: {len(dis)}")
w("DONE (not saved)")
