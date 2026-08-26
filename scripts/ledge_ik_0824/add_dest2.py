from mono import *
L="/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge"; FN="LedgeDebugIKPoints"
bq=lambda a,p: call("blueprint_query",a,p); P=lambda **k: dict(asset_path=L,graph_name=FN,**k)
KML="KismetMathLibrary"; KSL="KismetSystemLibrary"; BLACK="(R=0.0,G=0.0,B=0.0,A=1.0)"; GRAY="(R=0.3,G=0.3,B=0.3,A=1.0)"
g=bq("get_graph_data",{"asset_path":L,"graph_name":FN}); N={n["id"]:n for n in g["nodes"]}
br=[i for i,n in N.items() if "Break SBLedge" in n["title"]][0]
# Dest1 박스 4개 → 회색
for i in ("K2Node_CallFunction_67","K2Node_CallFunction_68","K2Node_CallFunction_69","K2Node_CallFunction_70"):
    bq("set_pin_default",P(node_id=i,pin_name="LineColor",value=GRAY))
def add(nt,pos,**kw):
    p=P(node_type=nt,position=[int(pos[0]),int(pos[1])]); p.update(kw); return bq("add_node",p)["id"]
def con(s,sp,t,tp):
    r=bq("connect_pins",P(source_node=s,source_pin=sp,target_node=t,target_pin=tp))
    if not r.get("success",True): print("CONNECT FAIL",s,sp,t,tp,r)
def dflt(n,pin,v): bq("set_pin_default",P(node_id=n,pin_name=pin,value=v))
# ── 공용 데이터 블록 (x 19600~20800, y 64~)
X0=19700
inp=add("CallFunction",(X0,64),function_name="GetLastMovementInputVector",target_class="Pawn"); con(add("VariableGet",(X0-230,64),variable_name="SBCharacter"),"SBCharacter",inp,"self")
tan=add("CallFunction",(X0,192),function_name="GetDirectionAtDistanceAlongSpline",target_class="SplineComponent")
con(add("VariableGet",(X0-230,192),variable_name="LedgeSplineRef"),"LedgeSplineRef",tan,"self"); con(add("VariableGet",(X0-230,256),variable_name="LedgeMoveTargetDist"),"LedgeMoveTargetDist",tan,"Distance"); dflt(tan,"CoordinateSpace","World")
dot=add("CallFunction",(X0+230,128),function_name="Dot_VectorVector",target_class=KML); con(inp,"ReturnValue",dot,"A"); con(tan,"ReturnValue",dot,"B")
ab=add("CallFunction",(X0+460,64),function_name="Abs",target_class=KML); con(dot,"ReturnValue",ab,"A")
gt=add("CallFunction",(X0+690,64),function_name="Greater_DoubleDouble",target_class=KML); con(ab,"ReturnValue",gt,"A"); dflt(gt,"B","0.3")
an=add("CallFunction",(X0+920,64),function_name="BooleanAND",target_class=KML); con(gt,"ReturnValue",an,"A"); con(br,"bUnitMoveInProgress",an,"B")
brQ=add("Branch",(X0+1150,0)); con(an,"ReturnValue",brQ,"Condition"); con("K2Node_CallFunction_70","then",brQ,"execute")
sg=add("CallFunction",(X0+460,192),function_name="SignOfFloat",target_class=KML); con(dot,"ReturnValue",sg,"A")
mul=add("CallFunction",(X0+690,192),function_name="Multiply_DoubleDouble",target_class=KML); con(sg,"ReturnValue",mul,"A"); con(br,"UnitSize",mul,"B")
ad=add("CallFunction",(X0+920,192),function_name="Add_DoubleDouble",target_class=KML); con(mul,"ReturnValue",ad,"A"); con(add("VariableGet",(X0+690,256),variable_name="LedgeMoveTargetDist"),"LedgeMoveTargetDist",ad,"B")
ln=add("CallFunction",(X0+920,320),function_name="GetSplineLength",target_class="SplineComponent"); con(add("VariableGet",(X0+690,320),variable_name="LedgeSplineRef"),"LedgeSplineRef",ln,"self")
cl=add("CallFunction",(X0+1150,192),function_name="FClamp",target_class=KML); con(ad,"ReturnValue",cl,"Value"); dflt(cl,"Min","0.0"); con(ln,"ReturnValue",cl,"Max")
tf=add("CallFunction",(X0+1380,192),function_name="GetTransformAtDistanceAlongSpline",target_class="SplineComponent"); con(add("VariableGet",(X0+1150,256),variable_name="LedgeSplineRef"),"LedgeSplineRef",tf,"self"); con(cl,"ReturnValue",tf,"Distance"); dflt(tf,"CoordinateSpace","World")
bt=add("CallFunction",(X0+1610,192),function_name="BreakTransform",target_class=KML); con(tf,"ReturnValue",bt,"InTransform")
brot=add("CallFunction",(X0+1840,256),function_name="BreakRotator",target_class=KML); con(bt,"Rotation",brot,"InRot")
mrot=add("CallFunction",(X0+2070,256),function_name="MakeRotator",target_class=KML); con(brot,"Yaw",mrot,"Yaw")
mt=add("CallFunction",(X0+2300,192),function_name="MakeTransform",target_class=KML); con(bt,"Location",mt,"Location"); con(mrot,"ReturnValue",mt,"Rotation"); dflt(mt,"Scale","1.0,1.0,1.0")
# ── 박스 4개: exec 행, 각 밴드 아래 앵커 변환
prev=(brQ,"then"); bx=X0+1150+480
for k,anc in enumerate(("LedgeHandAnchorL","LedgeHandAnchorR","LedgeFootAnchorL","LedgeFootAnchorR")):
    x=bx+k*1000
    inv=add("CallFunction",(x-460,64),function_name="InverseTransformLocation",target_class=KML)
    con(add("VariableGet",(x-690,64),variable_name="LedgeMoveStartT"),"LedgeMoveStartT",inv,"T"); con(add("VariableGet",(x-690,128),variable_name=anc),anc,inv,"Location")
    tl=add("CallFunction",(x-230,64),function_name="TransformLocation",target_class=KML); con(mt,"ReturnValue",tl,"T"); con(inv,"ReturnValue",tl,"Location")
    box=add("CallFunction",(x,0),function_name="DrawDebugBox",target_class=KSL); con(tl,"ReturnValue",box,"Center")
    dflt(box,"Extent","3.0,3.0,3.0"); dflt(box,"LineColor",BLACK); dflt(box,"Duration","0.0"); dflt(box,"Thickness","1.5")
    con(prev[0],prev[1],box,"execute"); prev=(box,"then")
c=bq("compile_blueprint",{"asset_path":L}); print("COMPILE",c.get("success"),c.get("errors"))
g=bq("get_graph_data",{"asset_path":L,"graph_name":FN}); bad=[(n["id"],n["title"].split("\n")[0],p["name"]) for n in g["nodes"] for p in n["pins"] if p["direction"]=="input" and p["type"]!="exec" and p["name"] not in ("self","Rotation","Segments","Min") and not p.get("connected_to") and p.get("default_value") in (None,"","0, 0, 0")]
print("nodes",len(g["nodes"]),"issues",bad)
print("saved",ed("save_packages",{"packages":[L]})["results"][0]["saved"])
