from mono import *
L="/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge"; FN="Ledge_HandTargetA"
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
ex={v["name"] for v in bq("get_variables",{"asset_path":L})["variables"]}
if "bLedgeHandA" not in ex: bq("add_variable",{"asset_path":L,"name":"bLedgeHandA","type":"bool","default_value":"true","category":"Ledge|HandA","instance_editable":True})
if FN not in [f["name"] for f in bq("get_functions",{"asset_path":L})["functions"]]:
    bq("add_function",{"asset_path":L,"name":FN,"category":"Ledge","description":"A안 손 타깃: 단위 이동 중 HandWorldL/R = Lerp(Anchor, T(TargetDist)×Inv(MoveStartT)×Anchor, clamp(ledge_hand_move)). 회색 도착 박스와 동일 수식. bLedgeHandA=false면 무동작."})
    bq("set_function_params",{"asset_path":L,"function_name":FN,"inputs":[{"name":"TgtDist","type":"float"},{"name":"bMoving","type":"bool"}]})
N=graph(); entry=[i for i,n in N.items() if "FunctionEntry" in n["class"]][0]
brA=add("Branch",(300,0)); con(entry,"then",brA,"execute"); con(get("bLedgeHandA",(70,64)),"bLedgeHandA",brA,"Condition")
nt=fn("Not_PreBool",(500,128)); con(get("LedgeTransitActive",(270,128)),"LedgeTransitActive",nt,"A")
iv=add("IsValid",(500,192)); con(get("LedgeSplineRef",(270,192)),"LedgeSplineRef",iv,"Object")
a1=fn("BooleanAND",(730,96)); con(entry,"bMoving",a1,"A"); con(nt,"ReturnValue",a1,"B")
a2=fn("BooleanAND",(960,96)); con(a1,"ReturnValue",a2,"A"); con(iv,"ReturnValue",a2,"B")
brG=add("Branch",(1200,0)); con(brA,"then",brG,"execute"); con(a2,"ReturnValue",brG,"Condition")
# T(Tgt) yaw-only (공용)
tf=fn("GetTransformAtDistanceAlongSpline",(1300,300),"SplineComponent"); con(get("LedgeSplineRef",(1070,300)),"LedgeSplineRef",tf,"self"); con(entry,"TgtDist",tf,"Distance"); dflt(tf,"CoordinateSpace","World")
bt=fn("BreakTransform",(1530,300)); con(tf,"ReturnValue",bt,"InTransform")
br=fn("BreakRotator",(1760,364)); con(bt,"Rotation",br,"InRot"); mr=fn("MakeRotator",(1990,364)); con(br,"Yaw",mr,"Yaw")
mt=fn("MakeTransform",(2220,300)); con(bt,"Location",mt,"Location"); con(mr,"ReturnValue",mt,"Rotation"); dflt(mt,"Scale","1.0,1.0,1.0")
prev=(brG,"then")
for k,S in enumerate(("L","R")):
    x=2900+k*1200; y=64
    inv=fn("InverseTransformLocation",(x-920,y+128)); con(get("LedgeMoveStartT",(x-1150,y+128)),"LedgeMoveStartT",inv,"T"); con(get("LedgeHandAnchor"+S,(x-1150,y+192)),"LedgeHandAnchor"+S,inv,"Location")
    tl=fn("TransformLocation",(x-690,y+128)); con(mt,"ReturnValue",tl,"T"); con(inv,"ReturnValue",tl,"Location")
    cv=add("CallFunction",(x-920,y),function_name="GetCurveValue",target_class="AnimInstance"); dflt(cv,"CurveName","ledge_hand_move_"+S.lower())
    cl=fn("FClamp",(x-690,y)); con(cv,"ReturnValue",cl,"Value"); dflt(cl,"Min","0.0"); dflt(cl,"Max","1.0")
    lp=fn("VLerp",(x-460,y)); con(get("LedgeHandAnchor"+S,(x-690,y+64)),"LedgeHandAnchor"+S,lp,"A"); con(tl,"ReturnValue",lp,"B"); con(cl,"ReturnValue",lp,"Alpha")
    s=setv("LedgeHandWorld"+S,(x,0)); con(lp,"ReturnValue",s,"LedgeHandWorld"+S); con(prev[0],prev[1],s,"execute"); prev=(s,"then")
c=bq("compile_blueprint",{"asset_path":L}); print("COMPILE",c.get("success"),c.get("errors"))
N=graph(); bad=[(i,n["title"].split("\n")[0],p["name"]) for i,n in N.items() for p in n["pins"] if p["direction"]=="input" and p["type"]!="exec" and p["name"] not in ("self","Min") and not p.get("connected_to") and p.get("default_value") in (None,"","0, 0, 0") and not p.get("default_object")]
print("nodes",len(N),"issues",bad)
if c.get("success"):
    G="LedgeIK"; Q=lambda **k: dict(asset_path=L,graph_name=G,**k)
    r=bq("add_node",Q(node_type="CallFunction",function_name=FN,target_class="PC_01_AnimLayer_Ledge_C",position=[3072,300])); nid=r["id"]
    bq("disconnect_pins",Q(node_id="K2Node_CallFunction_132",pin_name="then"))
    for s,sp,t,tp in [("K2Node_CallFunction_132","then",nid,"execute"),(nid,"then","K2Node_CallFunction_3","execute"),("K2Node_Knot_6","OutputPin",nid,"TgtDist"),("K2Node_Knot_10","OutputPin",nid,"bMoving")]:
        print(sp,"->",tp,bq("connect_pins",Q(source_node=s,source_pin=sp,target_node=t,target_pin=tp)).get("success"))
    c=bq("compile_blueprint",{"asset_path":L}); print("COMPILE2",c.get("success"),c.get("errors"))
    if c.get("success"): print("saved",ed("save_packages",{"packages":[L]})["results"][0]["saved"])
