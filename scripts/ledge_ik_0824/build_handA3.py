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
G="LedgeIK"; Q=lambda **k: dict(asset_path=L,graph_name=G,**k)
NI={n["id"]:n for n in bq("get_graph_data",{"asset_path":L,"graph_name":G})["nodes"]}
old=[i for i,n in NI.items() if n["title"].startswith("Ledge Hand Target A")]
for i in old: bq("remove_node",Q(node_id=i))
if FN in [f["name"] for f in bq("get_functions",{"asset_path":L})["functions"]]: bq("remove_function",{"asset_path":L,"name":FN})
ex={v["name"] for v in bq("get_variables",{"asset_path":L})["variables"]}
for n,t,d in [("bLedgeHandA","bool","true"),("LedgeA_PrevMoving","bool",None),("LedgeA_ArmedL","bool",None),("LedgeA_ArmedR","bool",None)]:
    if n not in ex:
        p={"asset_path":L,"name":n,"type":t,"category":"Ledge|HandA","instance_editable":n=="bLedgeHandA"}
        if d: p["default_value"]=d
        bq("add_variable",p)
bq("add_function",{"asset_path":L,"name":FN,"category":"Ledge","description":"A안 v3 손 타깃: 이동 중 HandWorld=Lerp(Anchor, T(Tgt)xInv(StartT)xAnchor, alpha). alpha=Armed? max(curve,progress):progress. Armed=이동 시작 후 커브<0.5 한 번 관측. 게이트: bMoving, Tgt==LedgeMoveTargetDist, Tgt!=StartDist, !Transit, IsValid(Spline). bLedgeHandA=false면 무동작."})
bq("set_function_params",{"asset_path":L,"function_name":FN,"inputs":[{"name":"CurDist","type":"float"},{"name":"TgtDist","type":"float"},{"name":"bMoving","type":"bool"}]})
N=graph(); entry=[i for i,n in N.items() if "FunctionEntry" in n["class"]][0]
brA=add("Branch",(300,0)); con(entry,"then",brA,"execute"); con(get("bLedgeHandA",(70,64)),"bLedgeHandA",brA,"Condition")
nt=fn("Not_PreBool",(500,128)); con(get("LedgeTransitActive",(270,128)),"LedgeTransitActive",nt,"A")
iv=add("IsValid",(500,192)); con(get("LedgeSplineRef",(270,192)),"LedgeSplineRef",iv,"Object")
eq=fn("EqualEqual_DoubleDouble",(500,256)); con(entry,"TgtDist",eq,"A"); con(get("LedgeMoveTargetDist",(270,256)),"LedgeMoveTargetDist",eq,"B")
ne=fn("NotEqual_DoubleDouble",(500,320)); con(entry,"TgtDist",ne,"A"); con(get("LedgeMoveStartDist",(270,320)),"LedgeMoveStartDist",ne,"B")
a1=fn("BooleanAND",(730,96)); con(entry,"bMoving",a1,"A"); con(nt,"ReturnValue",a1,"B")
a2=fn("BooleanAND",(960,96)); con(a1,"ReturnValue",a2,"A"); con(iv,"ReturnValue",a2,"B")
a3=fn("BooleanAND",(1190,96)); con(a2,"ReturnValue",a3,"A"); con(eq,"ReturnValue",a3,"B")
a4=fn("BooleanAND",(1420,96)); con(a3,"ReturnValue",a4,"A"); con(ne,"ReturnValue",a4,"B")
brG=add("Branch",(1700,0)); con(brA,"then",brG,"execute"); con(a4,"ReturnValue",brG,"Condition")
sPM0=setv("LedgeA_PrevMoving",(2000,300)); con(brG,"else",sPM0,"execute"); dflt(sPM0,"LedgeA_PrevMoving","false")
sAL0=setv("LedgeA_ArmedL",(2300,300)); con(sPM0,"then",sAL0,"execute"); dflt(sAL0,"LedgeA_ArmedL","false")
sAR0=setv("LedgeA_ArmedR",(2600,300)); con(sAL0,"then",sAR0,"execute"); dflt(sAR0,"LedgeA_ArmedR","false")
sPM1=setv("LedgeA_PrevMoving",(2000,0)); con(brG,"then",sPM1,"execute"); dflt(sPM1,"LedgeA_PrevMoving","true")
sub1=fn("Subtract_DoubleDouble",(1900,500)); con(entry,"CurDist",sub1,"A"); con(get("LedgeMoveStartDist",(1670,500)),"LedgeMoveStartDist",sub1,"B")
sub2=fn("Subtract_DoubleDouble",(1900,580)); con(entry,"TgtDist",sub2,"A"); con(get("LedgeMoveStartDist",(1670,580)),"LedgeMoveStartDist",sub2,"B")
dv=fn("Divide_DoubleDouble",(2130,540)); con(sub1,"ReturnValue",dv,"A"); con(sub2,"ReturnValue",dv,"B")
prog=fn("FClamp",(2360,540)); con(dv,"ReturnValue",prog,"Value"); dflt(prog,"Min","0.0"); dflt(prog,"Max","1.0")
tf=fn("GetTransformAtDistanceAlongSpline",(1900,700),"SplineComponent"); con(get("LedgeSplineRef",(1670,700)),"LedgeSplineRef",tf,"self"); con(entry,"TgtDist",tf,"Distance"); dflt(tf,"CoordinateSpace","World")
bt=fn("BreakTransform",(2130,700)); con(tf,"ReturnValue",bt,"InTransform")
br=fn("BreakRotator",(2360,764)); con(bt,"Rotation",br,"InRot"); mr=fn("MakeRotator",(2590,764)); con(br,"Yaw",mr,"Yaw")
mt=fn("MakeTransform",(2820,700)); con(bt,"Location",mt,"Location"); con(mr,"ReturnValue",mt,"Rotation"); dflt(mt,"Scale","1.0,1.0,1.0")
prev=(sPM1,"then")
for k,S in enumerate(("L","R")):
    x=3400+k*1900; y=64
    cv=add("CallFunction",(x-1150,y),function_name="GetCurveValue",target_class="AnimInstance"); dflt(cv,"CurveName","ledge_hand_move_"+S.lower())
    cl=fn("FClamp",(x-920,y)); con(cv,"ReturnValue",cl,"Value"); dflt(cl,"Min","0.0"); dflt(cl,"Max","1.0")
    lt=fn("Less_DoubleDouble",(x-690,y)); con(cl,"ReturnValue",lt,"A"); dflt(lt,"B","0.5")
    orA=fn("BooleanOR",(x-460,y)); con(lt,"ReturnValue",orA,"A"); con(get("LedgeA_Armed"+S,(x-690,y+64)),"LedgeA_Armed"+S,orA,"B")
    sArm=setv("LedgeA_Armed"+S,(x-230,0)); con(orA,"ReturnValue",sArm,"LedgeA_Armed"+S); con(prev[0],prev[1],sArm,"execute")
    mx=fn("FMax",(x-460,y+128)); con(cl,"ReturnValue",mx,"A"); con(prog,"ReturnValue",mx,"B")
    sel=fn("SelectFloat",(x-230,y+128)); con(mx,"ReturnValue",sel,"A"); con(prog,"ReturnValue",sel,"B"); con(get("LedgeA_Armed"+S,(x-460,y+192)),"LedgeA_Armed"+S,sel,"bPickA")
    inv=fn("InverseTransformLocation",(x-460,y+280)); con(get("LedgeMoveStartT",(x-690,y+280)),"LedgeMoveStartT",inv,"T"); con(get("LedgeHandAnchor"+S,(x-690,y+344)),"LedgeHandAnchor"+S,inv,"Location")
    tl=fn("TransformLocation",(x-230,y+280)); con(mt,"ReturnValue",tl,"T"); con(inv,"ReturnValue",tl,"Location")
    lp=fn("VLerp",(x+50,y+128)); con(get("LedgeHandAnchor"+S,(x-230,y+220)),"LedgeHandAnchor"+S,lp,"A"); con(tl,"ReturnValue",lp,"B"); con(sel,"ReturnValue",lp,"Alpha")
    s=setv("LedgeHandWorld"+S,(x+300,0)); con(lp,"ReturnValue",s,"LedgeHandWorld"+S); con(sArm,"then",s,"execute"); prev=(s,"then")
c=bq("compile_blueprint",{"asset_path":L}); print("COMPILE",c.get("success"),c.get("errors"))
N=graph(); bad=[(i,n["title"].split("\n")[0],p["name"]) for i,n in N.items() for p in n["pins"] if p["direction"]=="input" and p["type"]!="exec" and p["name"] not in ("self","Min") and not p.get("connected_to") and p.get("default_value") in (None,"","0, 0, 0") and not p.get("default_object")]
print("nodes",len(N),"issues",bad)
if c.get("success"):
    r=bq("add_node",Q(node_type="CallFunction",function_name=FN,target_class="PC_01_AnimLayer_Ledge_C",position=[3072,300])); nid=r["id"]
    bq("disconnect_pins",Q(node_id="K2Node_CallFunction_132",pin_name="then"))
    for s,sp,t,tp in [("K2Node_CallFunction_132","then",nid,"execute"),(nid,"then","K2Node_CallFunction_3","execute"),("K2Node_Knot_8","OutputPin",nid,"CurDist"),("K2Node_Knot_6","OutputPin",nid,"TgtDist"),("K2Node_Knot_10","OutputPin",nid,"bMoving")]:
        print(sp,"->",tp,bq("connect_pins",Q(source_node=s,source_pin=sp,target_node=t,target_pin=tp)).get("success"))
    c=bq("compile_blueprint",{"asset_path":L}); print("COMPILE2",c.get("success"),c.get("errors"))
    if c.get("success"): print("saved",ed("save_packages",{"packages":[L]})["results"][0]["saved"])
