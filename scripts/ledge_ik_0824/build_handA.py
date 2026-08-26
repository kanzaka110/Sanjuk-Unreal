# A안: Ledge_HandTargetA — 손 타깃 = Lerp(From, Dest, clamp(ledge_hand_move)) / 기존 함수 무수정, bLedgeHandA 스위치
import sys
from mono import *
L="/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge"; FN="Ledge_HandTargetA"
bq=lambda a,p: call("blueprint_query",a,p); P=lambda **k: dict(asset_path=L,graph_name=FN,**k)
KML="KismetMathLibrary"
def graph(): return {n["id"]:n for n in bq("get_graph_data",{"asset_path":L,"graph_name":FN})["nodes"]}
def add(nt,pos,**kw):
    p=P(node_type=nt,position=[int(pos[0]),int(pos[1])]); p.update(kw); rid=bq("add_node",p)["id"]
    N=graph()
    if rid in N: return rid
    c=[i for i,n in N.items() if n["pos"]==[int(pos[0]),int(pos[1])]]; print("stale",rid,"->",c); return c[-1]
def con(s,sp,t,tp):
    r=bq("connect_pins",P(source_node=s,source_pin=sp,target_node=t,target_pin=tp))
    if not r.get("success",True): print("CONNECT FAIL",s,sp,t,tp,r)
def dflt(n,pin,v):
    r=bq("set_pin_default",P(node_id=n,pin_name=pin,value=v))
    if not r.get("success",True): print("DEFAULT FAIL",n,pin,v,r)
get=lambda v,pos: add("VariableGet",pos,variable_name=v)
def setv(v,pos): return add("VariableSet",pos,variable_name=v)
def fn(name,pos,cls=KML): return add("CallFunction",pos,function_name=name,target_class=cls)

# ── 변수
existing={v["name"] for v in bq("get_variables",{"asset_path":L})["variables"]}
VARS=[("bLedgeHandA","bool","true",True),("LedgeA_RestDist","float",None,False),("LedgeA_PrevTgt","float",None,False),("LedgeA_PrevMoving","bool",None,False),
      ("LedgeA_FromL","struct:Vector",None,False),("LedgeA_FromR","struct:Vector",None,False),("LedgeA_DestL","struct:Vector",None,False),("LedgeA_DestR","struct:Vector",None,False)]
for n,t,d,e in VARS:
    if n in existing: continue
    p={"asset_path":L,"name":n,"type":t,"category":"Ledge|HandA","instance_editable":e}
    if d: p["default_value"]=d
    bq("add_variable",p); print("var",n)
# ── 함수
if FN not in [f["name"] for f in bq("get_functions",{"asset_path":L})["functions"]]:
    bq("add_function",{"asset_path":L,"name":FN,"category":"Ledge","description":"A안 손 타깃: 이동 중 HandWorldL/R = Lerp(From, Dest, clamp(ledge_hand_move)). Dest는 이동 시작/타깃 변경 엣지에 1회 래치(스플라인 Yaw 트랜스폼 × 앵커 상대좌표). bLedgeHandA=false면 무동작."})
    bq("set_function_params",{"asset_path":L,"function_name":FN,"inputs":[{"name":"CurDist","type":"float"},{"name":"TgtDist","type":"float"},{"name":"bMoving","type":"bool"}]})
N=graph(); entry=[i for i,n in N.items() if "FunctionEntry" in n["class"]][0]

# ── T(d) 빌더: 스플라인 d 위치 Yaw-only 트랜스폼 (5노드), 왼쪽 열 x, 기준 y
def Tof(dist_src,x,y):
    tf=fn("GetTransformAtDistanceAlongSpline",(x,y),"SplineComponent"); con(get("LedgeSplineRef",(x-230,y)),"LedgeSplineRef",tf,"self"); con(dist_src[0],dist_src[1],tf,"Distance"); dflt(tf,"CoordinateSpace","World")
    bt=fn("BreakTransform",(x+230,y)); con(tf,"ReturnValue",bt,"InTransform")
    br=fn("BreakRotator",(x+460,y+64)); con(bt,"Rotation",br,"InRot")
    mr=fn("MakeRotator",(x+690,y+64)); con(br,"Yaw",mr,"Yaw")
    mt=fn("MakeTransform",(x+920,y)); con(bt,"Location",mt,"Location"); con(mr,"ReturnValue",mt,"Rotation"); dflt(mt,"Scale","1.0,1.0,1.0")
    return mt

# ── exec: Entry → brA(bLedgeHandA) → brGate(moving && !transit && valid) 
brA=add("Branch",(300,0)); con(entry,"then",brA,"execute"); con(get("bLedgeHandA",(70,64)),"bLedgeHandA",brA,"Condition")
nt=fn("Not_PreBool",(500,128)); con(get("LedgeTransitActive",(270,128)),"LedgeTransitActive",nt,"A")
iv=add("IsValid",(500,192)); con(get("LedgeSplineRef",(270,192)),"LedgeSplineRef",iv,"Object")
a1=fn("BooleanAND",(730,96)); con(entry,"bMoving",a1,"A"); con(nt,"ReturnValue",a1,"B")
a2=fn("BooleanAND",(960,96)); con(a1,"ReturnValue",a2,"A"); con(iv,"ReturnValue",a2,"B")
brG=add("Branch",(1200,0)); con(brA,"then",brG,"execute"); con(a2,"ReturnValue",brG,"Condition")
# ── 정지: RestDist=CurDist, PrevMoving=false
sR=setv("LedgeA_RestDist",(1500,300)); con(brG,"else",sR,"execute"); con(entry,"CurDist",sR,"LedgeA_RestDist")
sPM0=setv("LedgeA_PrevMoving",(1800,300)); con(sR,"then",sPM0,"execute"); dflt(sPM0,"LedgeA_PrevMoving","false")
# ── 이동: 엣지 = !PrevMoving OR TgtDist != PrevTgt
npm=fn("Not_PreBool",(1300,128)); con(get("LedgeA_PrevMoving",(1070,128)),"LedgeA_PrevMoving",npm,"A")
ne=fn("NotEqual_DoubleDouble",(1300,192)); con(entry,"TgtDist",ne,"A"); con(get("LedgeA_PrevTgt",(1070,192)),"LedgeA_PrevTgt",ne,"B")
orr=fn("BooleanOR",(1530,128)); con(npm,"ReturnValue",orr,"A"); con(ne,"ReturnValue",orr,"B")
brE=add("Branch",(1800,0)); con(brG,"then",brE,"execute"); con(orr,"ReturnValue",brE,"Condition")
# ── 엣지 래치 블록 (y 400~)
Y=420
pm=get("LedgeA_PrevMoving",(1900,Y))
baseD=fn("SelectFloat",(2130,Y)); con(pm,"LedgeA_PrevMoving",baseD,"bPickA"); con(get("LedgeA_PrevTgt",(1900,Y+64)),"LedgeA_PrevTgt",baseD,"A"); con(get("LedgeA_RestDist",(1900,Y+128)),"LedgeA_RestDist",baseD,"B")
Tb=Tof((baseD,"ReturnValue"),2360,Y)          # T(base)
Tt=Tof((entry,"TgtDist"),2360,Y+260)          # T(tgt)
pm2=get("LedgeA_PrevMoving",(3500,Y+520))
def side(S,y):
    baseP=fn("SelectVector",(3730,y)); con(pm2,"LedgeA_PrevMoving",baseP,"bPickA"); con(get("LedgeA_Dest"+S,(3500,y)),"LedgeA_Dest"+S,baseP,"A"); con(get("LedgeHandAnchor"+S,(3500,y+64)),"LedgeHandAnchor"+S,baseP,"B")
    inv=fn("InverseTransformLocation",(3960,y)); con(Tb,"ReturnValue",inv,"T"); con(baseP,"ReturnValue",inv,"Location")
    tl=fn("TransformLocation",(4190,y)); con(Tt,"ReturnValue",tl,"T"); con(inv,"ReturnValue",tl,"Location")
    frm=fn("SelectVector",(3730,y+128)); con(pm2,"LedgeA_PrevMoving",frm,"bPickA"); con(get("LedgeHandWorld"+S,(3500,y+128)),"LedgeHandWorld"+S,frm,"A"); con(get("LedgeHandAnchor"+S,(3500,y+192)),"LedgeHandAnchor"+S,frm,"B")
    return tl,frm
dL,fL=side("L",Y+520); dR,fR=side("R",Y+780)
sFL=setv("LedgeA_FromL",(2100,0)); con(brE,"then",sFL,"execute"); con(fL,"ReturnValue",sFL,"LedgeA_FromL")
sFR=setv("LedgeA_FromR",(2400,0)); con(sFL,"then",sFR,"execute"); con(fR,"ReturnValue",sFR,"LedgeA_FromR")
sDL=setv("LedgeA_DestL",(2700,0)); con(sFR,"then",sDL,"execute"); con(dL,"ReturnValue",sDL,"LedgeA_DestL")
sDR=setv("LedgeA_DestR",(3000,0)); con(sDL,"then",sDR,"execute"); con(dR,"ReturnValue",sDR,"LedgeA_DestR")
sPT=setv("LedgeA_PrevTgt",(3300,0)); con(sDR,"then",sPT,"execute"); con(entry,"TgtDist",sPT,"LedgeA_PrevTgt")
sPM1=setv("LedgeA_PrevMoving",(3600,0)); con(sPT,"then",sPM1,"execute"); dflt(sPM1,"LedgeA_PrevMoving","true")
# ── 매 틱 Lerp → HandWorldL/R  (엣지 then/else 합류)
def lerp(S,x):
    cv=add("CallFunction",(x-690,64),function_name="GetCurveValue",target_class="AnimInstance"); dflt(cv,"CurveName","ledge_hand_move_"+S.lower())
    cl=fn("FClamp",(x-460,64)); con(cv,"ReturnValue",cl,"Value"); dflt(cl,"Min","0.0"); dflt(cl,"Max","1.0")
    lp=fn("VLerp",(x-230,64)); con(get("LedgeA_From"+S,(x-460,128)),"LedgeA_From"+S,lp,"A"); con(get("LedgeA_Dest"+S,(x-460,192)),"LedgeA_Dest"+S,lp,"B"); con(cl,"ReturnValue",lp,"Alpha")
    s=setv("LedgeHandWorld"+S,(x,0)); con(lp,"ReturnValue",s,"LedgeHandWorld"+S); return s
hL=lerp("L",4600); hR=lerp("R",5500)
con(sPM1,"then",hL,"execute"); con(brE,"else",hL,"execute"); con(hL,"then",hR,"execute")
c=bq("compile_blueprint",{"asset_path":L}); print("COMPILE",c.get("success"),c.get("errors"))
N=graph(); bad=[(i,n["title"].split("\n")[0],p["name"]) for i,n in N.items() for p in n["pins"] if p["direction"]=="input" and p["type"]!="exec" and p["name"] not in ("self","Min") and not p.get("connected_to") and p.get("default_value") in (None,"","0, 0, 0")]
print("nodes",len(N),"issues",bad)
