from mono import *
L="/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge"; FN="Ledge_HandTargetA"; A="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
bq=lambda a,p: call("blueprint_query",a,p); P=lambda **k: dict(asset_path=L,graph_name=FN,**k); KML="KismetMathLibrary"; KSL="KismetStringLibrary"
def graph(): return {n["id"]:n for n in bq("get_graph_data",{"asset_path":L,"graph_name":FN})["nodes"]}
def add(nt,pos,**kw):
    p=P(node_type=nt,position=[int(pos[0]),int(pos[1])]); p.update(kw); rid=bq("add_node",p)["id"]; N=graph()
    return rid if rid in N else [i for i,n in N.items() if n["pos"]==[int(pos[0]),int(pos[1])]][-1]
con=lambda s,sp,t,tp: bq("connect_pins",P(source_node=s,source_pin=sp,target_node=t,target_pin=tp)); dflt=lambda n,pin,v: bq("set_pin_default",P(node_id=n,pin_name=pin,value=v))
get=lambda v,pos: add("VariableGet",pos,variable_name=v); setv=lambda v,pos: add("VariableSet",pos,variable_name=v); fn=lambda name,pos,cls=KML: add("CallFunction",pos,function_name=name,target_class=cls)
ex={v["name"] for v in bq("get_variables",{"asset_path":L})["variables"]}
if "LedgeA_DebugLog" not in ex: bq("add_variable",{"asset_path":L,"name":"LedgeA_DebugLog","type":"string","category":"Ledge|HandA"})
N=graph(); entry="K2Node_FunctionEntry_0"
sHR=[i for i,n in N.items() if n["title"].startswith("Set LedgeHandWorldR")][0]; pos=N[sHR]["pos"]
lpL=[i for i,n in N.items() if n["title"].startswith("Lerp (Vector)") and any(p["name"]=="A" and p.get("connected_to") and p["connected_to"][0].endswith("FromL") for p in n["pins"])][0]
lpR=[i for i,n in N.items() if n["title"].startswith("Lerp (Vector)") and any(p["name"]=="A" and p.get("connected_to") and p["connected_to"][0].endswith("FromR") for p in n["pins"])][0]
aL=[c for p in N[lpL]["pins"] if p["name"]=="Alpha" for c in p["connected_to"]][0].rsplit(".",1); aR=[c for p in N[lpR]["pins"] if p["name"]=="Alpha" for c in p["connected_to"]][0].rsplit(".",1)
cvL=[i for i,n in N.items() if n["title"].startswith("Get Curve Value") and any(p.get("default_value")=="ledge_hand_move_l" for p in n["pins"])][0]
cvR=[i for i,n in N.items() if n["title"].startswith("Get Curve Value") and any(p.get("default_value")=="ledge_hand_move_r" for p in n["pins"])][0]
w=[i for i,n in N.items() if n["title"].startswith("Clamp (Float)") and any(c.split(".")[0] in N and N[c.split(".")[0]]["title"].startswith("float - float") and any(q["name"]=="A" and q.get("default_value")=="1.0" for q in N[c.split(".")[0]]["pins"]) for p in n["pins"] if p["name"]=="ReturnValue" for c in (p.get("connected_to") or []))][0]
parts=[("t",("LedgeA_Elapsed",None)),("w",(None,(w,"ReturnValue"))),("cL",(None,(cvL,"ReturnValue"))),("eL",("LedgeA_EdgeCvL",None)),("aL",(None,tuple(aL))),("cR",(None,(cvR,"ReturnValue"))),("eR",("LedgeA_EdgeCvR",None)),("aR",(None,tuple(aR))),("tg",(None,(entry,"TgtDist")))]
x=pos[0]+300; y=pos[1]+300; acc=None
for k,(lab,(var,src)) in enumerate(parts):
    cs=fn("Conv_DoubleToString",(x+k*260,y+120),KSL)
    if var: con(get(var,(x+k*260-200,y+120)),var,cs,"InDouble")
    else: con(src[0],src[1],cs,"InDouble")
    cc=fn("Concat_StrStr",(x+k*260,y+60),KSL); dflt(cc,"A",f" {lab}="); con(cs,"ReturnValue",cc,"B")
    if acc is None: acc=cc
    else: j=fn("Concat_StrStr",(x+k*260,y),KSL); con(acc,"ReturnValue",j,"A"); con(cc,"ReturnValue",j,"B"); acc=j
bs=fn("Conv_BoolToString",(x+len(parts)*260,y+120),KSL); con(entry,"bMoving",bs,"InBool")
bc=fn("Concat_StrStr",(x+len(parts)*260,y+60),KSL); dflt(bc,"A"," mv="); con(bs,"ReturnValue",bc,"B")
j=fn("Concat_StrStr",(x+len(parts)*260,y),KSL); con(acc,"ReturnValue",j,"A"); con(bc,"ReturnValue",j,"B"); acc=j
nl=fn("Concat_StrStr",(x+(len(parts)+1)*260,y),KSL); con(acc,"ReturnValue",nl,"A"); dflt(nl,"B"," |")
ap=fn("Concat_StrStr",(x+(len(parts)+2)*260,y),KSL); con(get("LedgeA_DebugLog",(x+(len(parts)+2)*260-200,y+60)),"LedgeA_DebugLog",ap,"A"); con(nl,"ReturnValue",ap,"B")
rt=fn("Right",(x+(len(parts)+3)*260,y),KSL); con(ap,"ReturnValue",rt,"SourceString"); dflt(rt,"Count","6000")
sl=setv("LedgeA_DebugLog",(x+(len(parts)+4)*260,pos[1])); con(rt,"ReturnValue",sl,"LedgeA_DebugLog"); con(sHR,"then",sl,"execute")
c=bq("compile_blueprint",{"asset_path":L}); print("LAYER COMPILE",c.get("success"),[e["message"][:80] for e in c.get("errors",[])])
bq("set_function_params",{"asset_path":L,"function_name":"LedgeState","outputs":[{"name":"DebugLog","type":"string"}]})
NS={n["id"]:n for n in bq("get_graph_data",{"asset_path":L,"graph_name":"LedgeState"})["nodes"]}; ret=[i for i,n in NS.items() if "FunctionResult" in n["class"]][0]; rp=NS[ret]["pos"]
vg=bq("add_node",{"asset_path":L,"graph_name":"LedgeState","node_type":"VariableGet","variable_name":"LedgeA_DebugLog","position":[rp[0]-260,rp[1]+760]})["id"]; bq("connect_pins",{"asset_path":L,"graph_name":"LedgeState","source_node":vg,"source_pin":"LedgeA_DebugLog","target_node":ret,"target_pin":"DebugLog"})
for xx in bq("search_nodes",{"asset_path":L,"query":"Ledge State"})["results"]:
    if xx["class"]=="K2Node_CallFunction": bq("refresh_node",{"asset_path":L,"graph_name":xx["graph"],"node_id":xx["node_id"]})
c=bq("compile_blueprint",{"asset_path":L}); print("LAYER COMPILE2",c.get("success"),[e["message"][:80] for e in c.get("errors",[])])
if c.get("success"): print("layer saved",ed("save_packages",{"packages":[L]})["results"][0]["saved"])
FA="GetLedgeIKDebugMirror"; Q=lambda **k: dict(asset_path=A,graph_name=FA,**k)
bq("refresh_node",Q(node_id="K2Node_CallFunction_1")); bq("set_function_params",{"asset_path":A,"function_name":FA,"outputs":[{"name":"DebugLog","type":"string"}]})
print("abp wire",bq("connect_pins",Q(source_node="K2Node_CallFunction_1",source_pin="DebugLog",target_node="K2Node_FunctionResult_0",target_pin="DebugLog")).get("success"))
c=bq("compile_blueprint",{"asset_path":A}); print("ABP COMPILE",c.get("success"),[e["message"][:80] for e in c.get("errors",[])])
