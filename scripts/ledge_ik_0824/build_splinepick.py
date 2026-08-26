from mono import *
L="/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge"; FN="Ledge_SplinePick"
bq=lambda a,p: call("blueprint_query",a,p); P=lambda **k: dict(asset_path=L,graph_name=FN,**k)
KML="KismetMathLibrary"
def graph(): return {n["id"]:n for n in bq("get_graph_data",{"asset_path":L,"graph_name":FN})["nodes"]}
def add(nt,pos,**kw):
    p=P(node_type=nt,position=[int(pos[0]),int(pos[1])]); p.update(kw); rid=bq("add_node",p)["id"]; N=graph()
    if rid in N: return rid
    c=[i for i,n in N.items() if n["pos"]==[int(pos[0]),int(pos[1])]]; print("stale",rid,"->",c); return c[-1]
def con(s,sp,t,tp):
    r=bq("connect_pins",P(source_node=s,source_pin=sp,target_node=t,target_pin=tp))
    if not r.get("success",True): print("CONNECT FAIL",s,sp,t,tp,r)
def dflt(n,pin,v):
    r=bq("set_pin_default",P(node_id=n,pin_name=pin,value=v))
    if not r.get("success",True): print("DEFAULT FAIL",n,pin,v,r)
get=lambda v,pos: add("VariableGet",pos,variable_name=v)
setv=lambda v,pos: add("VariableSet",pos,variable_name=v)
fn=lambda name,pos,cls=KML: add("CallFunction",pos,function_name=name,target_class=cls)

if FN not in [f["name"] for f in bq("get_functions",{"asset_path":L})["functions"]]:
    bq("add_function",{"asset_path":L,"name":FN,"category":"Ledge","description":"매 틱 스플라인 재선택: 오버랩 액터의 SplineComponent 중 score=|최근접점−손기준점|+2|스플라인거리−CurDist| 최소를 고르고, LedgeSplineRef가 바뀌면 MoveStartDist/StartT 재래치. (렛지→렛지 전이 후 옛 스플라인 참조 잔존 버그 대응)"})
    bq("set_function_params",{"asset_path":L,"function_name":FN,"inputs":[{"name":"CurDist","type":"float"}]})
    ex={v["name"] for v in bq("get_variables",{"asset_path":L})["variables"]}
    if "LedgeSP_BestScore" not in ex: bq("add_variable",{"asset_path":L,"name":"LedgeSP_BestScore","type":"float","category":"Ledge|SplinePick"})
    if "LedgeSP_BestComp" not in ex: bq("add_variable",{"asset_path":L,"name":"LedgeSP_BestComp","type":"object:SplineComponent","category":"Ledge|SplinePick"})
N=graph(); entry=[i for i,n in N.items() if "FunctionEntry" in n["class"]][0]
# 손기준점
sel=fn("SelectVector",(70,200)); dflt(sel,"A","5.23,-3.75,167.07"); dflt(sel,"B","7.19,-1.85,166.34"); con(get("LedgeFBLatch",(-160,200)),"LedgeFBLatch",sel,"bPickA")
href=fn("TransformLocation",(300,200)); con(get("LedgeMeshToWorld",(70,264)),"LedgeMeshToWorld",href,"T"); con(sel,"ReturnValue",href,"Location")
# init BestScore
sBS=setv("LedgeSP_BestScore",(300,0)); con(entry,"then",sBS,"execute"); dflt(sBS,"LedgeSP_BestScore","1000000000.0")
# overlap
pawn=fn("TryGetPawnOwner",(70,330),"AnimInstance"); ov=fn("GetOverlappingActors",(300,330),"Actor"); con(pawn,"ReturnValue",ov,"self")
loop=add("ForEachLoop",(700,0)); con(sBS,"then",loop,"Exec"); con(ov,"OverlappingActors",loop,"Array")
# body
comp=fn("GetComponentByClass",(1000,120),"Actor"); con(loop,"Array Element",comp,"self"); dflt(comp,"ComponentClass","/Script/Engine.SplineComponent")
iv=add("IsValid",(1230,120)); con(comp,"ReturnValue",iv,"Object")
brV=add("Branch",(1450,0)); con(loop,"LoopBody",brV,"execute"); con(iv,"ReturnValue",brV,"Condition")
dal=fn("GetDistanceAlongSplineAtLocation",(1700,200),"SplineComponent"); con(comp,"ReturnValue",dal,"self"); con(href,"ReturnValue",dal,"InLocation"); dflt(dal,"CoordinateSpace","World")
cp=fn("FindLocationClosestToWorldLocation",(1700,300),"SplineComponent"); con(comp,"ReturnValue",cp,"self"); con(href,"ReturnValue",cp,"WorldLocation"); dflt(cp,"CoordinateSpace","World")
dist=fn("Vector_Distance",(1930,300)); con(cp,"ReturnValue",dist,"V1"); con(href,"ReturnValue",dist,"V2")
sub=fn("Subtract_DoubleDouble",(1930,200)); con(dal,"ReturnValue",sub,"A"); con(entry,"CurDist",sub,"B")
ab=fn("Abs",(2160,200)); con(sub,"ReturnValue",ab,"A")
mul=fn("Multiply_DoubleDouble",(2390,200)); con(ab,"ReturnValue",mul,"A"); dflt(mul,"B","2.0")
score=fn("Add_DoubleDouble",(2620,250)); con(dist,"ReturnValue",score,"A"); con(mul,"ReturnValue",score,"B")
lt=fn("Less_DoubleDouble",(2850,250)); con(score,"ReturnValue",lt,"A"); con(get("LedgeSP_BestScore",(2620,330)),"LedgeSP_BestScore",lt,"B")
brB=add("Branch",(3100,0)); con(brV,"then",brB,"execute"); con(lt,"ReturnValue",brB,"Condition")
sS=setv("LedgeSP_BestScore",(3400,0)); con(brB,"then",sS,"execute"); con(score,"ReturnValue",sS,"LedgeSP_BestScore")
sC=setv("LedgeSP_BestComp",(3700,0)); con(sS,"then",sC,"execute"); con(comp,"ReturnValue",sC,"LedgeSP_BestComp")
# completed: best valid && != ref → 교체 + 재래치
bc=get("LedgeSP_BestComp",(4000,200)); iv2=add("IsValid",(4230,200)); con(bc,"LedgeSP_BestComp",iv2,"Object")
neq=fn("NotEqual_ObjectObject",(4230,280)); con(bc,"LedgeSP_BestComp",neq,"A"); con(get("LedgeSplineRef",(4000,280)),"LedgeSplineRef",neq,"B")
an=fn("BooleanAND",(4460,240)); con(iv2,"ReturnValue",an,"A"); con(neq,"ReturnValue",an,"B")
brR=add("Branch",(4700,0)); con(loop,"Completed",brR,"execute"); con(an,"ReturnValue",brR,"Condition")
sRef=setv("LedgeSplineRef",(5000,0)); con(brR,"then",sRef,"execute"); con(get("LedgeSP_BestComp",(4770,64)),"LedgeSP_BestComp",sRef,"LedgeSplineRef")
sSD=setv("LedgeMoveStartDist",(5300,0)); con(sRef,"then",sSD,"execute"); con(entry,"CurDist",sSD,"LedgeMoveStartDist")
tf=fn("GetTransformAtDistanceAlongSpline",(5000,200),"SplineComponent"); con(get("LedgeSP_BestComp",(4770,200)),"LedgeSP_BestComp",tf,"self"); con(entry,"CurDist",tf,"Distance"); dflt(tf,"CoordinateSpace","World")
bt=fn("BreakTransform",(5230,200)); con(tf,"ReturnValue",bt,"InTransform")
br=fn("BreakRotator",(5460,264)); con(bt,"Rotation",br,"InRot"); mr=fn("MakeRotator",(5690,264)); con(br,"Yaw",mr,"Yaw")
mt=fn("MakeTransform",(5920,200)); con(bt,"Location",mt,"Location"); con(mr,"ReturnValue",mt,"Rotation"); dflt(mt,"Scale","1.0,1.0,1.0")
sST=setv("LedgeMoveStartT",(6200,0)); con(sSD,"then",sST,"execute"); con(mt,"ReturnValue",sST,"LedgeMoveStartT")
c=bq("compile_blueprint",{"asset_path":L}); print("COMPILE",c.get("success"),c.get("errors"))
N=graph(); bad=[(i,n["title"].split("\n")[0],p["name"]) for i,n in N.items() for p in n["pins"] if p["direction"]=="input" and p["type"]!="exec" and p["name"] not in ("self","Min","Array Index") and not p.get("connected_to") and p.get("default_value") in (None,"","0, 0, 0")]
print("nodes",len(N),"issues",bad)
