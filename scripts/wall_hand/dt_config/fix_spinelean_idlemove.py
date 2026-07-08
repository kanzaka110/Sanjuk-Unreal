"""Split side SpineLeanMaxDeg into Idle/Move. CF_134 = front?FWall:CF_133(side _Move).
Add sideIdle select(CF_9?R:L _Idle) + switch(isMoving CF_150 ? sideMove CF_133 : sideIdle).
CF_134.B <- switch. Front (FWall) unchanged (no idle/move split there). reuse CF_150(speed>80).
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
RB,LB="K2Node_BreakStruct_0","K2Node_BreakStruct_1"; CF9=("K2Node_CallFunction_9","ReturnValue"); ISMOVING=("K2Node_CallFunction_150","ReturnValue")
def idlepin(nid):
    d=C("get_node_details",node_id=nid); return next(p['name'] for p in d['pins'] if p['direction']=='output' and p['name'].startswith('SpineLeanMaxDeg_Idle'))
IR,IL=idlepin(RB),idlepin(LB)
w(f"Idle pins R={IR} L={IL}")
def sel(pos): return C("add_node",node_type="CallFunction",function_name="SelectFloat",target_class="KismetMathLibrary",position=pos).get("id")
# sideIdle = CF_9 ? R._Idle : L._Idle
si=sel([2900,1500]); conn(RB,IR,si,"A","idle sR"); conn(LB,IL,si,"B","idle sL"); conn(CF9[0],CF9[1],si,"bPickA","idle sCF9")
# switch = isMoving ? sideMove(CF_133) : sideIdle
sw=sel([3150,1420]); conn("K2Node_CallFunction_133","ReturnValue",sw,"A","sw.A=Move"); conn(si,"ReturnValue",sw,"B","sw.B=Idle"); conn(ISMOVING[0],ISMOVING[1],sw,"bPickA","sw.bPickA=isMoving")
# CF_134.B <- switch
C("disconnect_pins",node_id="K2Node_CallFunction_134",pin_name="B")
conn(sw,"ReturnValue","K2Node_CallFunction_134","B","sw->CF_134.B")
r=C("compile_blueprint"); w(f"[compile] success={r.get('success')} err={r.get('error_count')}")
if r.get('errors'): w("  ERR:"+str(r['errors']))
w(f"sideIdle={si} switch={sw}")
w("DONE (not saved)")
