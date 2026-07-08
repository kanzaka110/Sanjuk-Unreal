"""Wire IdleFollow + idle/move switch. Currently follow always uses MoveFollow.Pct (CF_136).
Add: IdleFollow.Pct 3-way (front?FWall:(CF_9?R:L)) + switch (speed>80 ? MoveFollow : IdleFollow).
Reconnect CF_100.B <- switch. speed = CF_51 (VectorLengthXY, reused). threshold 80 (backup).
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
FAIL=[]
def conn(sn,sp,tn,tp,tag):
    r=C("connect_pins",source_node=sn,source_pin=sp,target_node=tn,target_pin=tp); ok=r.get('success')
    w(f"   {tag}: {ok}"+("" if ok else f" {r}"));
    if not ok: FAIL.append(tag)
RB,LB,FB="K2Node_BreakStruct_0","K2Node_BreakStruct_1","K2Node_BreakStruct_2"
CF9=("K2Node_CallFunction_9","ReturnValue"); GATE=("K2Node_CallFunction_53","ReturnValue")
def fld(nid,short):
    d=C("get_node_details",node_id=nid); return next(p['name'] for p in d['pins'] if p['direction']=='output' and p['name'].split('_')[0]==short)
def breakfollow(src_break, pos):
    r=C("add_node",node_type="break_struct",struct_type="S_WallHandFollow",position=pos); bid=r.get("id")
    d=C("get_node_details",node_id=bid); inp=[p['name'] for p in d['pins'] if p['direction']=='input'][0]
    pct=next(p['name'] for p in d['pins'] if p['direction']=='output' and p['name'].split('_')[0]=='Pct')
    idle=fld(src_break,'IdleFollow')
    conn(src_break,idle,bid,inp,f"IdleFollow->break")
    return bid,pct
def sel(pos): return C("add_node",node_type="CallFunction",function_name="SelectFloat",target_class="KismetMathLibrary",position=pos).get("id")

# IdleFollow.Pct per wall
bfR,pR=breakfollow(RB,[600,-1000]); bfL,pL=breakfollow(LB,[600,-920]); bfF,pF=breakfollow(FB,[600,-840])
# side select (CF_9) + front select (gate)
ss=sel([850,-980]); conn(bfR,pR,ss,"A","idle sR"); conn(bfL,pL,ss,"B","idle sL"); conn(CF9[0],CF9[1],ss,"bPickA","idle sCF9")
fs=sel([1050,-960]); conn(bfF,pF,fs,"A","idle fF"); conn(ss,"ReturnValue",fs,"B","idle fB"); conn(GATE[0],GATE[1],fs,"bPickA","idle fGate")
# isMoving = CF_51 > 80
r=C("add_node",node_type="CallFunction",function_name="Greater_DoubleDouble",target_class="KismetMathLibrary",position=[1050,-760]); mv=r.get("id")
w(f"isMoving(>)={mv}")
conn("K2Node_CallFunction_51","ReturnValue",mv,"A","speed->mv.A"); C("set_pin_default",node_id=mv,pin_name="B",value="80.0")
# switch: A=MoveFollow(CF_136), B=IdleFollow(fs), bPickA=isMoving
sw=sel([1300,-900])
conn("K2Node_CallFunction_136","ReturnValue",sw,"A","sw.A=Move"); conn(fs,"ReturnValue",sw,"B","sw.B=Idle"); conn(mv,"ReturnValue",sw,"bPickA","sw.bPickA=isMoving")
# reconnect CF_100.B <- switch
C("disconnect_pins",node_id="K2Node_CallFunction_100",pin_name="B")
conn(sw,"ReturnValue","K2Node_CallFunction_100","B","sw->CF_100.B")

r=C("compile_blueprint"); w(f"[compile] success={r.get('success')} err={r.get('error_count')}")
if r.get('errors'): w("  ERR:"+str(r['errors']))
w(f"idleFollowFinal={fs} switch={sw} FAILS={FAIL}")
w("DONE (not saved)")
