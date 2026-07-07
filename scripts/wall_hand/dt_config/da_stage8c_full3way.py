"""Stage 8c: full front?(FWall):(bRight?RWall:LWall) for AttachStartDist/FullDist(CF_21),
SpineLeanMaxDeg(CF_95.B), MoveFollow.Pct(CF_100.B). Adds FWall/LWall MoveFollow breaks.
Behavior CHANGE: front wall now uses FWall attach-dist/spine/follow (were RWall). R=L neutral.
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
def sel(pos):
    return C("add_node",node_type="CallFunction",function_name="SelectFloat",target_class="KismetMathLibrary",position=pos).get("id")

RB,LB,FB="K2Node_BreakStruct_0","K2Node_BreakStruct_1","K2Node_BreakStruct_2"
GATE=("K2Node_CallFunction_53","ReturnValue"); BRIGHT=("K2Node_CallFunction_54","bRight")
def flds(nid):
    d=C("get_node_details",node_id=nid); return {p['name'].split('_')[0]:p['name'] for p in d['pins'] if p['direction']=='output'}
rf,lf,ff=flds(RB),flds(LB),flds(FB)

# full 3-way for a scalar field -> reconnect target pin
def full3(field, target_node, target_pin, y):
    ss=sel([2400,y]); fs=sel([2650,y])
    conn(RB,rf[field],ss,"A",f"{field} sR"); conn(LB,lf[field],ss,"B",f"{field} sL"); conn(BRIGHT[0],BRIGHT[1],ss,"bPickA",f"{field} sBR")
    conn(FB,ff[field],fs,"A",f"{field} fF"); conn(ss,"ReturnValue",fs,"B",f"{field} fB"); conn(GATE[0],GATE[1],fs,"bPickA",f"{field} fGate")
    conn(fs,"ReturnValue",target_node,target_pin,f"{field} -> {target_node}.{target_pin}")

full3("AttachStartDist","K2Node_CallFunction_21","InRangeA",-1900)
full3("AttachFullDist","K2Node_CallFunction_21","InRangeB",-1820)
full3("SpineLeanMaxDeg","K2Node_CallFunction_95","B",-1740)

# MoveFollow.Pct: break FWall & LWall MoveFollow (RWall=BreakStruct_3 exists), select Pct
w("MoveFollow.Pct 3-way")
def breakfollow(src_break, field, pos):
    r=C("add_node",node_type="break_struct",struct_type="S_WallHandFollow",position=pos); bid=r.get("id")
    dd=C("get_node_details",node_id=bid); inp=[p['name'] for p in dd['pins'] if p['direction']=='input'][0]
    pct=next(p['name'] for p in dd['pins'] if p['direction']=='output' and p['name'].split('_')[0]=='Pct')
    conn(src_break, {'F':ff,'L':lf}[field[0]][field[1]], bid, inp, f"{field}->break")
    return bid,pct
bfF,pctF=breakfollow(FB,("F","MoveFollow"),[2200,-1640])
bfL,pctL=breakfollow(LB,("L","MoveFollow"),[2200,-1560])
# RWall Pct from existing BreakStruct_3
dd=C("get_node_details",node_id="K2Node_BreakStruct_3"); pctR=next(p['name'] for p in dd['pins'] if p['direction']=='output' and p['name'].split('_')[0]=='Pct')
ss=sel([2400,-1600]); fs=sel([2650,-1600])
conn("K2Node_BreakStruct_3",pctR,ss,"A","MF.Pct sR"); conn(bfL,pctL,ss,"B","MF.Pct sL"); conn(BRIGHT[0],BRIGHT[1],ss,"bPickA","MF.Pct sBR")
conn(bfF,pctF,fs,"A","MF.Pct fF"); conn(ss,"ReturnValue",fs,"B","MF.Pct fB"); conn(GATE[0],GATE[1],fs,"bPickA","MF.Pct fGate")
conn(fs,"ReturnValue","K2Node_CallFunction_100","B","MF.Pct -> CF_100.B")

r=C("compile_blueprint"); w(f"[compile] success={r.get('success')} err={r.get('error_count')} warn={r.get('warning_count')}")
if r.get('errors'): w("  ERRORS: "+str(r['errors']))
r2=C("validate_blueprint"); dis=[x for x in (r2.get('disconnected_nodes') or []) if x.get('graph')=='UpdateWallHandIK']
w(f"  disconnected: {len(dis)}  FAILS: {FAIL}")
w("DONE (not saved)")
