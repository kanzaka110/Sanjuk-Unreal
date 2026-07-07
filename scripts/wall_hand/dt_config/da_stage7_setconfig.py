"""Stage 7: add SetWallHandConfig call (missing in reverted BP) -> delivers ALL remaining DA
fields to ABP (which has the attach/release/turn/elbow logic). Each input = front-overlay
select(CF_53 ? FWall.field : RWall.field). Elbow -> DegreesToRadians. RelRangeMin/Max=100/450 lit.
Additive subtree + 1 exec insert after GetWallHandState(CF_54). Compile+validate. No save.
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
    r=C("connect_pins",source_node=sn,source_pin=sp,target_node=tn,target_pin=tp)
    ok=r.get('success'); w(f"   {tag}: {ok}"+("" if ok else f"  {r}"));
    if not ok: FAIL.append(tag)
def addsel(pos):
    r=C("add_node",node_type="CallFunction",function_name="SelectFloat",target_class="KismetMathLibrary",position=pos); return r.get("id")
def addbv(pos):
    r=C("add_node",node_type="CallFunction",function_name="BreakVector2D",target_class="KismetMathLibrary",position=pos); return r.get("id")

RB,FB="K2Node_BreakStruct_0","K2Node_BreakStruct_2"
GATE="K2Node_CallFunction_53"   # front gate (AND)
SELFSRC="K2Node_Knot_23"        # ABP self routing
def flds(nid):
    d=C("get_node_details",node_id=nid); return {p['name'].split('_')[0]:p['name'] for p in d['pins'] if p['direction']=='output'}
rf,ff=flds(RB),flds(FB)

# 1. SetWallHandConfig call
r=C("add_node",node_type="CallFunction",function_name="SetWallHandConfig",target_class="PC_01_ABP_C",position=[3300,-1500]); SC=r.get("id")
w(f"[1] SetWallHandConfig={SC}")
conn(SELFSRC,"OutputPin",SC,"self","self")

# helper: front-overlay scalar select A=FWall.<ffield>, B=RWall.<rfield> -> SC.<inpin>
def overlay(inpin, rfield, ffield, y):
    s=addsel([2900,y])
    conn(FB,ff[ffield],s,"A",f"{inpin}.A(F.{ffield})")
    conn(RB,rf[rfield],s,"B",f"{inpin}.B(R.{rfield})")
    conn(GATE,"ReturnValue",s,"bPickA",f"{inpin}.gate")
    conn(s,"ReturnValue",SC,inpin,f"{inpin}<-sel")
    return s

# 2. scalar overlays
overlay("InWHIKStrength","IKStrength","IKStrength",-1700)
overlay("InWHTurnRelSpd","TurnReleaseSpeed","TurnReleaseSpeed",-1620)
overlay("InWHTurnBlockHold","TurnBlockHold","TurnBlockHold",-1540)

# 3. AttachSpeed (V2D) -> Start(X)/End(Y); need BreakVec2D for FWall & RWall AttachSpeed
def v2d_overlay(field, startpin, endpin, y):
    bF=addbv([2500,y]); bR=addbv([2500,y+40])
    conn(FB,ff[field],bF,"InVec",f"{field} F->break")
    conn(RB,rf[field],bR,"InVec",f"{field} R->break")
    sX=addsel([2900,y]); sY=addsel([2900,y+40])
    conn(bF,"X",sX,"A",f"{startpin}.A"); conn(bR,"X",sX,"B",f"{startpin}.B"); conn(GATE,"ReturnValue",sX,"bPickA",f"{startpin}.gate"); conn(sX,"ReturnValue",SC,startpin,f"{startpin}<-sel")
    conn(bF,"Y",sY,"A",f"{endpin}.A"); conn(bR,"Y",sY,"B",f"{endpin}.B"); conn(GATE,"ReturnValue",sY,"bPickA",f"{endpin}.gate"); conn(sY,"ReturnValue",SC,endpin,f"{endpin}<-sel")
v2d_overlay("AttachSpeed","InWHAttachSpdStart","InWHAttachSpdEnd",-1440)
v2d_overlay("ReleaseSpeed","InWHRelSpdSlow","InWHRelSpdFast",-1340)

# 4. RelRange literals
w("[4] RelRange lits: "+str(C("set_pin_default",node_id=SC,pin_name="InWHRelRangeMin",value="100.0").get('success'))+","+str(C("set_pin_default",node_id=SC,pin_name="InWHRelRangeMax",value="450.0").get('success')))

# 5. Elbow: overlay(FWall.Elbow, RWall.Elbow) -> DegToRad -> InWHElbowRad
esel=addsel([2900,-1240])
conn(FB,ff["ElbowAngleDeg"],esel,"A","Elbow.A(F)"); conn(RB,rf["ElbowAngleDeg"],esel,"B","Elbow.B(R)"); conn(GATE,"ReturnValue",esel,"bPickA","Elbow.gate")
r=C("add_node",node_type="CallFunction",function_name="DegreesToRadians",target_class="KismetMathLibrary",position=[3100,-1240]); DR=r.get("id"); w(f"[5] DegToRad={DR} {'' if DR else r}")
if DR:
    # find input pin name
    dd=C("get_node_details",node_id=DR); inp=[p['name'] for p in dd['pins'] if p['direction']=='input'][0]
    conn(esel,"ReturnValue",DR,inp,"Elbow->DegToRad")
    conn(DR,"ReturnValue",SC,"InWHElbowRad","InWHElbowRad<-rad")

# 6. exec insert: CF_54.then -> SC -> Knot_46
w("[6] exec insert")
conn("K2Node_CallFunction_54","then",SC,"execute","54.then->SC.exec")
conn(SC,"then","K2Node_Knot_46","InputPin","SC.then->Knot_46")

# 7. verify
r=C("compile_blueprint"); w(f"[compile] success={r.get('success')} err={r.get('error_count')} warn={r.get('warning_count')}")
if r.get('errors'): w("  ERRORS: "+str(r['errors']))
r2=C("validate_blueprint"); dis=[x for x in (r2.get('disconnected_nodes') or []) if x.get('graph')=='UpdateWallHandIK']
w(f"  disconnected: {len(dis)}  FAILS: {FAIL}")
w("DONE (not saved)")
