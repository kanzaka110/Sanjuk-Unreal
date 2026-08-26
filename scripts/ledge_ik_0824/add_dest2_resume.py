from mono import *
L="/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge"; FN="LedgeDebugIKPoints"
bq=lambda a,p: call("blueprint_query",a,p); P=lambda **k: dict(asset_path=L,graph_name=FN,**k)
KML="KismetMathLibrary"; KSL="KismetSystemLibrary"; BLACK="(R=0.0,G=0.0,B=0.0,A=1.0)"
X0=19700; BX=X0+1150+480
def graph(): 
    g=bq("get_graph_data",{"asset_path":L,"graph_name":FN}); return {n["id"]:n for n in g["nodes"]}
N=graph()
brQ=[i for i,n in N.items() if n["title"].startswith("Branch") and n["pos"][0]==X0+1150][0]
mt=[i for i,n in N.items() if n["title"].startswith("Make Transform") and n["pos"][0]==X0+2300][0]
print("brQ",brQ,"mt",mt)
# 박스 구간 잔여물 제거 (x >= BX-700)
junk=[i for i,n in N.items() if n["pos"][0]>=BX-700 and i not in (brQ,mt)]
print("junk",junk)
for i in junk: bq("remove_node",P(node_id=i))
def add(nt,pos,**kw):
    p=P(node_type=nt,position=[int(pos[0]),int(pos[1])]); p.update(kw); rid=bq("add_node",p)["id"]
    N=graph()
    if rid in N: return rid
    cands=[i for i,n in N.items() if n["pos"]==[int(pos[0]),int(pos[1])]]
    print("stale id",rid,"->",cands); return cands[-1]
def con(s,sp,t,tp):
    r=bq("connect_pins",P(source_node=s,source_pin=sp,target_node=t,target_pin=tp))
    if not r.get("success",True): print("CONNECT FAIL",s,sp,t,tp,r)
def dflt(n,pin,v): bq("set_pin_default",P(node_id=n,pin_name=pin,value=v))
prev=(brQ,"then")
for k,anc in enumerate(("LedgeHandAnchorL","LedgeHandAnchorR","LedgeFootAnchorL","LedgeFootAnchorR")):
    x=BX+k*1000
    inv=add("CallFunction",(x-460,64),function_name="InverseTransformLocation",target_class=KML)
    v1=add("VariableGet",(x-690,64),variable_name="LedgeMoveStartT"); con(v1,"LedgeMoveStartT",inv,"T")
    v2=add("VariableGet",(x-690,128),variable_name=anc); con(v2,anc,inv,"Location")
    tl=add("CallFunction",(x-230,64),function_name="TransformLocation",target_class=KML); con(mt,"ReturnValue",tl,"T"); con(inv,"ReturnValue",tl,"Location")
    box=add("CallFunction",(x,0),function_name="DrawDebugBox",target_class=KSL); con(tl,"ReturnValue",box,"Center")
    dflt(box,"Extent","3.0,3.0,3.0"); dflt(box,"LineColor",BLACK); dflt(box,"Duration","0.0"); dflt(box,"Thickness","1.5")
    con(prev[0],prev[1],box,"execute"); prev=(box,"then")
c=bq("compile_blueprint",{"asset_path":L}); print("COMPILE",c.get("success"),c.get("errors"))
N=graph(); bad=[(i,n["title"].split("\n")[0],p["name"]) for i,n in N.items() for p in n["pins"] if p["direction"]=="input" and p["type"]!="exec" and p["name"] not in ("self","Rotation","Segments","Min") and not p.get("connected_to") and p.get("default_value") in (None,"","0, 0, 0")]
print("nodes",len(N),"issues",bad)
print("saved",ed("save_packages",{"packages":[L]})["results"][0]["saved"])
