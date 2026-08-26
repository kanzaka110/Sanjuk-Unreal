from mono import *
L="/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge"; FN="LedgeDebugIKPoints"
bq=lambda a,p: call("blueprint_query",a,p)
P=lambda **k: dict(asset_path=L,graph_name=FN,**k)
KML="KismetMathLibrary"; KSL="KismetSystemLibrary"; BLACK="(R=0.0,G=0.0,B=0.0,A=1.0)"
# 0) LedgeIK가 쓰는 무브먼트 변수명
g=bq("get_graph_data",{"asset_path":L,"graph_name":"LedgeIK"}); N={n["id"]:n for n in g["nodes"]}
selfsrc=[p["connected_to"] for p in N["K2Node_CallFunction_48"]["pins"] if p["name"]=="self"][0][0]
mv_var=[p["name"] for p in N[selfsrc.split(".")[0]]["pins"] if p["direction"]=="output"][0]; print("movement var:",mv_var)
# 1) 기존 전이 섹션 제거
g=bq("get_graph_data",{"asset_path":L,"graph_name":FN}); N={n["id"]:n for n in g["nodes"]}
brTr=[n for n in N.values() if n["title"].startswith("Branch") and any("LedgeTransitActive" in str(p.get("connected_to")) for p in n["pins"])][0]["id"]
kill=set([brTr])
def walk(nid):
    for p in N[nid]["pins"]:
        if p["type"]=="exec" and p["direction"]=="output":
            for c in p.get("connected_to") or []:
                t=c.split(".")[0]
                if t not in kill: kill.add(t); walk(t)
walk(brTr)
# 데이터 입력 노드(순수)도 제거: kill 노드의 입력에 연결된 노드 중 exec 없는 것
for nid in list(kill):
    for p in N[nid]["pins"]:
        if p["direction"]=="input" and p["type"]!="exec":
            for c in p.get("connected_to") or []:
                s=c.split(".")[0]
                if s in N and not any(q["type"]=="exec" for q in N[s]["pins"]): kill.add(s)
                # subtract 노드의 입력(VariableGet)도
for nid in list(kill):
    for p in N[nid]["pins"]:
        if p["direction"]=="input" and p["type"]!="exec":
            for c in p.get("connected_to") or []:
                s=c.split(".")[0]
                if s in N and "VariableGet" in N[s]["class"]: kill.add(s)
print("remove",sorted(kill))
for nid in kill: bq("remove_node",P(node_id=nid))
X=[3000]
def add(nt,**kw):
    X[0]+=220; p=P(node_type=nt,position=[X[0],600]); p.update(kw); return bq("add_node",p)["id"]
def con(s,sp,t,tp):
    r=bq("connect_pins",P(source_node=s,source_pin=sp,target_node=t,target_pin=tp))
    if not r.get("success",True): print("CONNECT FAIL",s,sp,t,tp,r)
def dflt(n,pin,v):
    r=bq("set_pin_default",P(node_id=n,pin_name=pin,value=v))
    if not r.get("success",True): print("DEFAULT FAIL",n,pin,v,r)
get=lambda v: add("VariableGet",variable_name=v)
# 2) 라이브 MoveData
md=add("CallFunction",function_name="GetLedgeMoveData",target_class="SBCharacterMovementComponent"); con(get(mv_var),mv_var,md,"self")
br=add("BreakStruct",struct_type="SBLedgeMoveData"); con(md,"ReturnValue",br,"SBLedgeMoveData")
lt=add("CallFunction",function_name="Less_FloatFloat",target_class=KML); con(br,"NextLedgeCandidateDist",lt,"A"); dflt(lt,"B","1000000000000.0")
brC=add("Branch"); con(lt,"ReturnValue",brC,"Condition")
# exec 재연결: 마지막 구 CF_31.then → brC, brMv.else → brC
brMv=[n["id"] for n in N.values() if n["title"].startswith("Branch") and any("LedgeUnitMoving" in str(p.get("connected_to")) for p in n["pins"])][0]
con("K2Node_CallFunction_31","then",brC,"execute"); con(brMv,"else",brC,"execute")
# 3) 손기준중심
sel=add("CallFunction",function_name="SelectVector",target_class=KML); dflt(sel,"A","5.23,-3.75,167.07"); dflt(sel,"B","7.19,-1.85,166.34"); con(get("LedgeFBLatch"),"LedgeFBLatch",sel,"bPickA")
ctr=add("CallFunction",function_name="TransformLocation",target_class=KML); con(get("LedgeMeshToWorld"),"LedgeMeshToWorld",ctr,"T"); con(sel,"ReturnValue",ctr,"Location")
prev=(brC,"then")
for anc in ("LedgeHandAnchorL","LedgeHandAnchorR","LedgeFootAnchorL","LedgeFootAnchorR"):
    sub=add("CallFunction",function_name="Subtract_VectorVector",target_class=KML); con(get(anc),anc,sub,"A"); con(ctr,"ReturnValue",sub,"B")
    ad=add("CallFunction",function_name="Add_VectorVector",target_class=KML); con(br,"NextLedgeCandidateClosest",ad,"A"); con(sub,"ReturnValue",ad,"B")
    box=add("CallFunction",function_name="DrawDebugBox",target_class=KSL); con(ad,"ReturnValue",box,"Center")
    dflt(box,"Extent","3.0,3.0,3.0"); dflt(box,"LineColor",BLACK); dflt(box,"Duration","0.0"); dflt(box,"Thickness","1.5")
    con(prev[0],prev[1],box,"execute"); prev=(box,"then")
c=bq("compile_blueprint",{"asset_path":L}); print("COMPILE",c.get("success"),c.get("errors"),c.get("warnings"))
