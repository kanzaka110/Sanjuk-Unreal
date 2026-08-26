import json, urllib.request
URL="http://localhost:9316/mcp"
BP="/Game/Developers/SHIFTUP/GameDesign/System/Users/JHJ/Map/InteractionTest/JHJ_InteractionTest_WP"
def call(tool, action, params, timeout=120):
    body={"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":tool,"arguments":{"action":action,"params":params}}}
    req=urllib.request.Request(URL,json.dumps(body).encode(),{"Content-Type":"application/json"})
    r=json.load(urllib.request.urlopen(req,timeout=timeout)); res=r["result"]; txt=res["content"][0]["text"]
    if res.get("isError"): raise RuntimeError(action+": "+txt[:600])
    return json.loads(txt)
bq=lambda a,p: call("blueprint_query",a,dict(asset_path=BP,**p))
def add(g,**k):
    r=bq("add_node",dict(graph_name=g,**k)); return r["id"],[p["name"] for p in r.get("pins",[])]
def con(g,s,sp,t,tp):
    try: bq("connect_pins",dict(graph_name=g,source_node=s,source_pin=sp,target_node=t,target_pin=tp)); print("OK",g,sp,"->",t,tp)
    except Exception as e: print("FAIL",g,s,sp,"->",t,tp,str(e)[:160])
def subsys(g,pos):
    n,_=add(g,node_type="GetSubsystem",position=pos); bq("set_pin_default",dict(graph_name=g,node_id=n,pin_name="Class",value="/Script/SB2.SBTransitDestinationSubsystem")); bq("refresh_node",dict(graph_name=g,node_id=n)); return n
def entry_ret(g):
    d=bq("get_graph_data",dict(graph_name=g)); e=r=None
    for n in d["nodes"]:
        if "FunctionEntry" in n["class"]: e=n["id"]
        if "FunctionResult" in n["class"]: r=n["id"]
    return e,r
# ---------- InitHookPoint(HookActor) -> Id, Offset
G1="InitHookPoint"
bq("remove_function",dict(name=G1)); bq("add_function",dict(name=G1))
print(bq("set_function_params",dict(function_name=G1,inputs=[{"name":"HookActor","type":"object:SBZoneEnvActor"}],outputs=[{"name":"Id","type":"struct:Guid"},{"name":"Offset","type":"struct:Vector"}])))
e,r=entry_ret(G1); print("entry/ret",e,r)
gf,_=add(G1,node_type="CallFunction",function_name="GetHookFeature",target_class="SBZoneEnvActor",position=[250,150])
gi,_=add(G1,node_type="CallFunction",function_name="GetRegistrationId",target_class="SBZoneEnvActorHookFeature",position=[480,150])
ss=subsys(G1,[480,300]); gd,_=add(G1,node_type="CallFunction",function_name="GetData",target_class="SBTransitDestinationSubsystem",position=[710,300])
br,_=add(G1,node_type="BreakStruct",struct_type="SBTransitDestinationData",position=[940,300])
gl,_=add(G1,node_type="CallFunction",function_name="K2_GetActorLocation",target_class="Actor",position=[940,500])
sub,_=add(G1,node_type="CallFunction",function_name="Subtract_VectorVector",target_class="KismetMathLibrary",position=[1170,400])
con(G1,e,"then",r,"execute"); con(G1,e,"HookActor",gf,"self"); con(G1,gf,"ReturnValue",gi,"self"); con(G1,gi,"ReturnValue",r,"Id")
con(G1,ss,"ReturnValue",gd,"self"); con(G1,gi,"ReturnValue",gd,"InId"); con(G1,gd,"OutData",br,"SBTransitDestinationData")
con(G1,e,"HookActor",gl,"self"); con(G1,br,"Location",sub,"A"); con(G1,gl,"ReturnValue",sub,"B"); con(G1,sub,"ReturnValue",r,"Offset")
# ---------- MoveHookPoint(Id, HookActor, Offset) -> NewId  : GetData -> Unregister -> Register(new loc)
G2="MoveHookPoint"
bq("remove_function",dict(name=G2)); bq("add_function",dict(name=G2))
print(bq("set_function_params",dict(function_name=G2,inputs=[{"name":"Id","type":"struct:Guid"},{"name":"HookActor","type":"object:SBZoneEnvActor"},{"name":"Offset","type":"struct:Vector"}],outputs=[{"name":"NewId","type":"struct:Guid"}])))
e,r=entry_ret(G2); print("entry/ret",e,r)
ss=subsys(G2,[250,300]); gd,_=add(G2,node_type="CallFunction",function_name="GetData",target_class="SBTransitDestinationSubsystem",position=[480,300])
br,_=add(G2,node_type="BreakStruct",struct_type="SBTransitDestinationData",position=[710,300])
mk=bq("add_node",dict(graph_name=G2,node_type="MakeStruct",struct_type="SBTransitDestinationData",position=[1170,300])); mkid=mk["id"]; fields=[p["name"] for p in mk["pins"] if p["name"]!="SBTransitDestinationData"]
gl,_=add(G2,node_type="CallFunction",function_name="K2_GetActorLocation",target_class="Actor",position=[710,700])
ad,_=add(G2,node_type="CallFunction",function_name="Add_VectorVector",target_class="KismetMathLibrary",position=[940,700])
un,_=add(G2,node_type="CallFunction",function_name="Unregister",target_class="SBTransitDestinationSubsystem",position=[480,0])
rg,_=add(G2,node_type="CallFunction",function_name="Register",target_class="SBTransitDestinationSubsystem",position=[1500,0])
con(G2,ss,"ReturnValue",gd,"self"); con(G2,e,"Id",gd,"InId"); con(G2,gd,"OutData",br,"SBTransitDestinationData")
con(G2,e,"HookActor",gl,"self"); con(G2,gl,"ReturnValue",ad,"A"); con(G2,e,"Offset",ad,"B")
for f in fields:
    if f=="Location": con(G2,ad,"ReturnValue",mkid,f)
    else: con(G2,br,f,mkid,f)
con(G2,e,"then",un,"execute"); con(G2,ss,"ReturnValue",un,"self"); con(G2,e,"Id",un,"InId")
con(G2,un,"then",rg,"execute"); con(G2,ss,"ReturnValue",rg,"self"); con(G2,mkid,"SBTransitDestinationData",rg,"InData")
con(G2,rg,"then",r,"execute"); con(G2,rg,"ReturnValue",r,"NewId")
c=bq("compile_blueprint",{}); print("COMPILE1",{k:c.get(k) for k in ("success","error_count","errors")})
