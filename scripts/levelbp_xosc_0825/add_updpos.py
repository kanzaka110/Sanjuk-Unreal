import json, urllib.request
URL="http://localhost:9316/mcp"
BP="/Game/Developers/SHIFTUP/GameDesign/System/Users/JHJ/Map/InteractionTest/JHJ_InteractionTest_WP"
LVL=BP+".JHJ_InteractionTest_WP:PersistentLevel."
HOOK="BP_EM_Hookshot_InAir_C_UAID_30560F6BCAE568FB02_1136314272"
def call(tool, action, params, timeout=120):
    body={"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":tool,"arguments":{"action":action,"params":params}}}
    req=urllib.request.Request(URL,json.dumps(body).encode(),{"Content-Type":"application/json"})
    r=json.load(urllib.request.urlopen(req,timeout=timeout)); res=r["result"]; txt=res["content"][0]["text"]
    if res.get("isError"): raise RuntimeError(action+": "+txt[:600])
    return json.loads(txt)
bq=lambda a,p: call("blueprint_query",a,dict(asset_path=BP,**p))
def add(**k):
    r=bq("add_node",k); print("ADD",r["id"],[p["name"] for p in r.get("pins",[])]); return r["id"]
def con(s,sp,t,tp):
    try: bq("connect_pins",dict(source_node=s,source_pin=sp,target_node=t,target_pin=tp)); print("OK",s,sp,"->",t,tp)
    except Exception as e: print("FAIL",s,sp,"->",t,tp,e)
def lit(pos):
    li=add(node_type="K2Node_Literal",position=pos)
    bq("set_node_property",dict(node_id=li,property_name="ObjectRef",value=LVL+HOOK)); bq("refresh_node",dict(node_id=li))
    return li,[p["name"] for p in bq("get_node_details",dict(node_id=li))["pins"]][0]
def subsys(pos):
    for nt,extra in [("GetSubsystem",dict(subsystem_class="SBTransitDestinationSubsystem")),("K2Node_GetSubsystem",dict(subsystem_class="SBTransitDestinationSubsystem")),("GetSubsystem",dict(class_name="SBTransitDestinationSubsystem"))]:
        try:
            r=bq("add_node",dict(node_type=nt,position=pos,**extra)); print("SUB",r["id"],[p["name"] for p in r["pins"]]); return r["id"]
        except Exception as e: print("sub fail",nt,extra,str(e)[:200])
    raise SystemExit("no subsystem node")
# cleanup ResetActor
bq("remove_node",dict(node_id="K2Node_CallFunction_24"))
for n in bq("get_graph_data",{})["nodes"]:
    if n["class"]=="K2Node_Literal" and not any(p.get("connected_to") for p in n["pins"]): bq("remove_node",dict(node_id=n["id"])); print("rm orphan lit",n["id"])
# vars
for name,typ in [("HookRegId","struct:Guid"),("HookPtOffset","vector")]:
    try: print(bq("add_variable",dict(name=name,type=typ)))
    except Exception as e: print("var",name,e)
# --- BeginPlay: after Set StartLoc_Hookshot12 (K2Node_VariableSet_2)
X=1800
sid=add(node_type="VariableSet",variable_name="HookRegId",position=[X,0])
li,lp=lit([X-690,150]); gf=add(node_type="CallFunction",function_name="GetHookFeature",target_class="SBZoneEnvActor",position=[X-460,150])
gi=add(node_type="CallFunction",function_name="GetRegistrationId",target_class="SBZoneEnvActorHookFeature",position=[X-230,150])
con("K2Node_VariableSet_2","then",sid,"execute"); con(li,lp,gf,"self"); con(gf,"ReturnValue",gi,"self"); con(gi,"ReturnValue",sid,"HookRegId")
X2=X+450
sof=add(node_type="VariableSet",variable_name="HookPtOffset",position=[X2,0])
ss=subsys([X2-920,150]); gd=add(node_type="CallFunction",function_name="GetData",target_class="SBTransitDestinationSubsystem",position=[X2-690,150])
gid=add(node_type="VariableGet",variable_name="HookRegId",position=[X2-920,250])
br=add(node_type="BreakStruct",struct_type="SBTransitDestinationData",position=[X2-460,150])
sub=add(node_type="CallFunction",function_name="Subtract_VectorVector",target_class="KismetMathLibrary",position=[X2-230,150])
gsl=add(node_type="VariableGet",variable_name="StartLoc_Hookshot12",position=[X2-460,400])
con(sid,"then",sof,"execute"); con(ss,"ReturnValue",gd,"self"); con(gid,"HookRegId",gd,"InId"); con(gd,"OutData",br,"SBTransitDestinationData")
con(br,"Location",sub,"A"); con(gsl,"StartLoc_Hookshot12",sub,"B"); con(sub,"ReturnValue",sof,"HookPtOffset")
# --- Update: after SetActorLocation hookshot (K2Node_CallFunction_9), new loc = K2Node_CallFunction_10.ReturnValue
X3=2250
up=add(node_type="CallFunction",function_name="UpdatePosition",target_class="SBTransitDestinationSubsystem",position=[X3,700])
ss2=subsys([X3-460,850]); gid2=add(node_type="VariableGet",variable_name="HookRegId",position=[X3-460,950])
ad=add(node_type="CallFunction",function_name="Add_VectorVector",target_class="KismetMathLibrary",position=[X3-230,1000])
gof=add(node_type="VariableGet",variable_name="HookPtOffset",position=[X3-460,1050])
con("K2Node_CallFunction_9","then",up,"execute"); con(ss2,"ReturnValue",up,"self"); con(gid2,"HookRegId",up,"InId")
con("K2Node_CallFunction_10","ReturnValue",ad,"A"); con(gof,"HookPtOffset",ad,"B"); con(ad,"ReturnValue",up,"InNewLocation")
c=bq("compile_blueprint",{}); print("COMPILE",{k:c.get(k) for k in ("success","error_count","warning_count","errors","warnings")})
