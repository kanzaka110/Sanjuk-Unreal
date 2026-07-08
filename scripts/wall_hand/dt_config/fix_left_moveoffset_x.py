"""Negate LEFT-wall X for move offsets (Jog/Run/Sprint) - same left-frame flip as HandOffset.X.
CF_1(Jog.X)/CF_30(Run.X)/CF_64(Sprint.X): B<-LWall.X (picked on left via CF_9). Insert *-1 on B.
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

# for each select, find current B source, insert Multiply(-1)
SELECTS={"K2Node_CallFunction_1":"Jog","K2Node_CallFunction_30":"Run","K2Node_CallFunction_64":"Sprint"}
y=520
for sel,lbl in SELECTS.items():
    d=C("get_node_details",node_id=sel)
    bsrc=next((p['connected_to'] for p in d['pins'] if p['name']=='B'),None)
    if not bsrc: w(f"{lbl}: B not connected, skip"); continue
    src_node,src_pin=bsrc[0].rsplit('.',1)
    w(f"{lbl}({sel}): B <- {src_node}.{src_pin}")
    C("disconnect_pins",node_id=sel,pin_name="B")
    m=C("add_node",node_type="CallFunction",function_name="Multiply_DoubleDouble",target_class="KismetMathLibrary",position=[1400,y]).get("id")
    r=C("connect_pins",source_node=src_node,source_pin=src_pin,target_node=m,target_pin="A"); w(f"   {src_pin}->Neg.A: {r.get('success')}")
    C("set_pin_default",node_id=m,pin_name="B",value="-1.0")
    r=C("connect_pins",source_node=m,source_pin="ReturnValue",target_node=sel,target_pin="B"); w(f"   Neg->{sel}.B: {r.get('success')}")
    y+=80
r=C("compile_blueprint"); w(f"[compile] success={r.get('success')} err={r.get('error_count')}")
if r.get('errors'): w("  ERR:"+str(r['errors']))
w("DONE (not saved)")
