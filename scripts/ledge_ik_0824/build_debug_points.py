# PC_01_AnimLayer_Ledge: 신규 디버그 함수 LedgeDebugIKPoints
#  1) 손/발 실시간 IK 타깃 박스 (빨강=On / 갈색=Off, 알파>0.5)
#  2) 이동 도착점 구 — Lerp(Anchor, SlideTgt, clamp(ledge_*_move 커브)) (LedgeUnitMoving 중)
#  3) 전이(끝/위아래) 도착 손발 작은 검정 박스 (LedgeTransitActive 중)
import json,sys
from mono import *
L="/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge"
FN="LedgeDebugIKPoints"
bq=lambda a,p: call("blueprint_query",a,p)
KML="KismetMathLibrary"; KSL="KismetSystemLibrary"
RED="(R=1.0,G=0.0,B=0.0,A=1.0)"; BROWN="(R=0.35,G=0.18,B=0.05,A=1.0)"; BLACK="(R=0.0,G=0.0,B=0.0,A=1.0)"; YEL="(R=1.0,G=0.85,B=0.0,A=1.0)"
X=[0]
def add(node_type,**kw):
    X[0]+=1
    p={"asset_path":L,"graph_name":FN,"node_type":node_type,"position":[X[0]*220,0]}; p.update(kw)
    r=bq("add_node",p); return r["id"]
def con(s,sp,t,tp):
    r=bq("connect_pins",{"asset_path":L,"graph_name":FN,"source_node":s,"source_pin":sp,"target_node":t,"target_pin":tp})
    if not r.get("success",True): print("CONNECT FAIL",s,sp,t,tp,r)
def dflt(n,pin,v):
    r=bq("set_pin_default",{"asset_path":L,"graph_name":FN,"node_id":n,"pin_name":pin,"value":v})
    if not r.get("success",True): print("DEFAULT FAIL",n,pin,v,r)
def get(var): return add("VariableGet",variable_name=var)
def fn(name,cls=None):
    kw={"function_name":name}
    if cls: kw["target_class"]=cls
    return add("CallFunction",**kw)

existing=[f["name"] for f in bq("get_functions",{"asset_path":L})["functions"]]
if FN in existing: print("exists — abort"); sys.exit(1)
print(bq("add_function",{"asset_path":L,"name":FN,"category":"Debug","description":"IK 디버그 포인트 3종: 실시간 IK 박스(빨강On/갈색Off)·이동 도착 구(move 커브 반영)·전이 도착 검정 박스. LedgeDebug 게이트."}))
g=bq("get_graph_data",{"asset_path":L,"graph_name":FN}); entry=[n["id"] for n in g["nodes"] if "FunctionEntry" in n["class"]][0]

# ── 게이트
brDbg=add("Branch"); con(entry,"then",brDbg,"execute"); con(get("LedgeDebug"),"LedgeDebug",brDbg,"Condition")
prev=(brDbg,"then")

# ── 1) 실시간 IK 박스
def ikbox(center_var,alpha_var):
    global prev
    gt=fn("Greater_DoubleDouble",KML); con(get(alpha_var),alpha_var,gt,"A"); dflt(gt,"B","0.5")
    sc=fn("SelectColor",KML); dflt(sc,"A",RED); dflt(sc,"B",BROWN); con(gt,"ReturnValue",sc,"bPickA")
    box=fn("DrawDebugBox",KSL); con(get(center_var),center_var,box,"Center"); con(sc,"ReturnValue",box,"LineColor")
    dflt(box,"Extent","6.0,6.0,6.0"); dflt(box,"Duration","0.0"); dflt(box,"Thickness","1.5")
    con(prev[0],prev[1],box,"execute"); prev=(box,"then")
for c,a in [("LedgeHandWorldPredL","LedgeHandIKAlphaL"),("LedgeHandWorldPredR","LedgeHandIKAlphaR"),
            ("LedgeFootWorldTargetL","LedgeFootIKAlphaL"),("LedgeFootWorldTargetR","LedgeFootIKAlphaR")]: ikbox(c,a)

# ── 2) 이동 도착 구 (커브 반영)
brMv=add("Branch"); con(get("LedgeUnitMoving"),"LedgeUnitMoving",brMv,"Condition"); con(prev[0],prev[1],brMv,"execute")
prev=(brMv,"then")
def movesphere(anchor,slide,curve):
    global prev
    cv=fn("GetCurveValue"); dflt(cv,"CurveName",curve)
    cl=fn("FClamp",KML); con(cv,"ReturnValue",cl,"Value"); dflt(cl,"Min","0.0"); dflt(cl,"Max","1.0")
    lp=fn("VLerp",KML); con(get(anchor),anchor,lp,"A"); con(get(slide),slide,lp,"B"); con(cl,"ReturnValue",lp,"Alpha")
    sp=fn("DrawDebugSphere",KSL); con(lp,"ReturnValue",sp,"Center"); dflt(sp,"Radius","4.0"); dflt(sp,"Segments","12"); dflt(sp,"LineColor",YEL); dflt(sp,"Duration","0.0"); dflt(sp,"Thickness","1.0")
    con(prev[0],prev[1],sp,"execute"); prev=(sp,"then")
for a,s,c in [("LedgeHandAnchorL","LedgeSlideTgtHL","ledge_hand_move_l"),("LedgeHandAnchorR","LedgeSlideTgtHR","ledge_hand_move_r"),
              ("LedgeFootAnchorL","LedgeSlideTgtFL","ledge_foot_move_l"),("LedgeFootAnchorR","LedgeSlideTgtFR","ledge_foot_move_r")]: movesphere(a,s,c)

# ── 3) 전이 도착 검정 박스
brTr=add("Branch"); con(get("LedgeTransitActive"),"LedgeTransitActive",brTr,"Condition")
con(prev[0],prev[1],brTr,"execute"); con(brMv,"else",brTr,"execute")
prev=(brTr,"then")
def blackbox(src_node,src_pin):
    global prev
    box=fn("DrawDebugBox",KSL); con(src_node,src_pin,box,"Center")
    dflt(box,"Extent","3.0,3.0,3.0"); dflt(box,"LineColor",BLACK); dflt(box,"Duration","0.0"); dflt(box,"Thickness","1.5")
    con(prev[0],prev[1],box,"execute"); prev=(box,"then")
for anc in ("LedgeHandAnchorL","LedgeHandAnchorR"):
    sub=fn("Subtract_VectorVector",KML); con(get(anc),anc,sub,"A"); con(get("LedgeUnitMoveVec"),"LedgeUnitMoveVec",sub,"B")
    blackbox(sub,"ReturnValue")
for fd in ("LedgeFootDestL","LedgeFootDestR"): blackbox(get(fd),fd)

g=bq("get_graph_data",{"asset_path":L,"graph_name":FN}); print("nodes",len(g["nodes"]))
c=bq("compile_blueprint",{"asset_path":L}); print("COMPILE",c.get("success"),c.get("errors"),c.get("warnings"))
