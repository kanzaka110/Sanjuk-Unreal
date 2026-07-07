"""Stage 1: DA read scaffold on reverted UpdateWallHandIK.
WallHandConfig var already added. Now: set default=DA asset, add GetConfig (exec-insert at start),
Break RWall/LWall/FWall. All additive except 1 exec re-route (Entry->GetConfig->SetSmoothVel).
Downstream break outputs left UNCONNECTED -> zero behavior change. Compile+validate. No save.
"""
import json, urllib.request
MCP="http://localhost:9316/mcp"; BP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"; G="UpdateWallHandIK"
DA="/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK/DA_WallHandIK.DA_WallHandIK"
def call(a,p):
    b={"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"blueprint_query","arguments":{"action":a,"params":p}}}
    r=urllib.request.Request(MCP,data=json.dumps(b).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=120) as x: raw=json.loads(x.read().decode())
    try:
        if "result" in raw and "content" in raw["result"]:
            t=raw["result"]["content"][0]["text"]
            return json.loads(t) if t.strip() else {"_raw":t,"success":None}
    except Exception as e:
        return {"_parse_error":str(e),"_raw":raw}
    return raw
def C(a,**p): p.update(asset_path=BP);
def Cg(a,**p): p.update(asset_path=BP,graph_name=G); return call(a,p)
def w(m): print(m)

# 0. set variable default = DA asset (CDO) -- best effort, non-fatal
try:
    r=call("set_cdo_property",{"asset_path":BP,"property_name":"WallHandConfig","value":DA})
    w(f"[0] set default: {r}")
except Exception as e:
    w(f"[0] set default FAILED (non-fatal): {e}")

# 1. VariableGet WallHandConfig
r=Cg("add_node",node_type="VariableGet",variable_name="WallHandConfig",position=[-5200,-1000]); VG=r.get("id")
w(f"[1] VariableGet WallHandConfig -> {VG}")

# 2. GetConfig call
r=Cg("add_node",node_type="CallFunction",function_name="GetConfig",target_class="PDA_WallHandIKConfig_C",position=[-4900,-1000]); GC=r.get("id")
w(f"[2] GetConfig -> {GC}")
det=Cg("get_node_details",node_id=GC)
w("    GetConfig pins: "+str([(p['name'],p['direction']) for p in det['pins']]))

# 3. self <- WallHandConfig
r=Cg("connect_pins",source_node=VG,source_pin="WallHandConfig",target_node=GC,target_pin="self")
w(f"[3] VG.WallHandConfig -> GetConfig.self: {r.get('success')} {r if not r.get('success') else ''}")

# 4. exec insert: Entry.then -> GetConfig.execute -> SetSmoothVel.execute
r=Cg("disconnect_pins",node_id="K2Node_VariableSet_0",pin_name="execute")
w(f"[4a] disconnect SetSmoothVel.execute: {r.get('success')}")
r=Cg("connect_pins",source_node="K2Node_FunctionEntry_0",source_pin="then",target_node=GC,target_pin="execute")
w(f"[4b] Entry.then -> GetConfig.execute: {r.get('success')} {r if not r.get('success') else ''}")
r=Cg("connect_pins",source_node=GC,source_pin="then",target_node="K2Node_VariableSet_0",target_pin="execute")
w(f"[4c] GetConfig.then -> SetSmoothVel.execute: {r.get('success')} {r if not r.get('success') else ''}")

# 5. Break R/L/F
breaks={}
for name,struct,out,pos in [("RWall","S_WallHandSideConfig","RWall",[-4600,-1200]),
                            ("LWall","S_WallHandSideConfig","LWall",[-4600,-1000]),
                            ("FWall","S_WallHandFrontConfig","FWall",[-4600,-800])]:
    r=Cg("add_node",node_type="break_struct",struct_type=struct,position=pos); bid=r.get("id"); breaks[name]=bid
    d=Cg("get_node_details",node_id=bid); inpin=[p['name'] for p in d['pins'] if p['direction']=='input'][0]
    r=Cg("connect_pins",source_node=GC,source_pin=out,target_node=bid,target_pin=inpin)
    w(f"[5] Break {name} -> {bid}, GetConfig.{out}->{inpin}: {r.get('success')}")

# 6. compile + validate
r=Cg("compile_blueprint")
w(f"[6] compile success={r.get('success')} err={r.get('error_count')} warn={r.get('warning_count')}")
if r.get('errors'): w("    ERRORS: "+str(r['errors']))
r2=Cg("validate_blueprint")
dis=[x for x in (r2.get('disconnected_nodes') or []) if x.get('graph')=='UpdateWallHandIK']
w(f"    disconnected in graph: {len(dis)}")
w("SCAFFOLD IDS: VG=%s GC=%s breaks=%s"%(VG,GC,breaks))
w("DONE (not saved)")
