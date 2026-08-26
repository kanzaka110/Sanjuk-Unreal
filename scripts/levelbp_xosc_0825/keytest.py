import json, urllib.request
URL="http://localhost:9316/mcp"
BP="/Game/Developers/SHIFTUP/GameDesign/System/Users/JHJ/Map/InteractionTest/JHJ_InteractionTest_WP"
LVL=BP+".JHJ_InteractionTest_WP:PersistentLevel."; HOOK="BP_EM_Hookshot_InAir_C_UAID_30560F6BCAE568FB02_1136314272"
def call(tool, action, params, timeout=120):
    body={"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":tool,"arguments":{"action":action,"params":params}}}
    req=urllib.request.Request(URL,json.dumps(body).encode(),{"Content-Type":"application/json"})
    r=json.load(urllib.request.urlopen(req,timeout=timeout)); res=r["result"]; txt=res["content"][0]["text"]
    if res.get("isError"): raise RuntimeError(action+": "+txt[:600])
    return json.loads(txt)
bq=lambda a,p: call("blueprint_query",a,dict(asset_path=BP,**p))
def add(**k):
    r=bq("add_node",k); print("ADD",r["id"],[p["name"] for p in r.get("pins",[])][:14]); return r["id"]
def con(s,sp,t,tp):
    try: bq("connect_pins",dict(source_node=s,source_pin=sp,target_node=t,target_pin=tp)); print("OK",s,sp,"->",t,tp)
    except Exception as e: print("FAIL",s,sp,"->",t,tp,str(e)[:160])
def subsys(pos):
    n=add(node_type="GetSubsystem",position=pos); bq("set_pin_default",dict(node_id=n,pin_name="Class",value="/Script/SB2.SBTransitDestinationSubsystem")); bq("refresh_node",dict(node_id=n)); return n
def lit(pos):
    li=add(node_type="K2Node_Literal",position=pos); bq("set_node_property",dict(node_id=li,property_name="ObjectRef",value=LVL+HOOK)); bq("refresh_node",dict(node_id=li))
    return li,[p["name"] for p in bq("get_node_details",dict(node_id=li))["pins"]][0]
def printstr(pos,prefix):
    p=add(node_type="CallFunction",function_name="PrintString",target_class="KismetSystemLibrary",position=pos)
    bq("set_pin_default",dict(node_id=p,pin_name="Duration",value="5")); return p
def keyev(key,pos):
    for nt,ex in [("InputKey",dict(key=key)),("K2Node_InputKey",dict(key=key)),("InputKey",dict(input_key=key))]:
        try: r=bq("add_node",dict(node_type=nt,position=pos,**ex)); print("KEY",r["id"],[p["name"] for p in r["pins"]]); return r["id"]
        except Exception as e: print("key fail",nt,str(e)[:120])
    raise SystemExit("no key node")
# check HookRegId still set in BeginPlay chain
d=bq("get_node_details",dict(node_id="K2Node_VariableSet_6")); print("HookRegId set exec:",[p.get("connected_to") for p in d["pins"] if p["name"]=="execute"])
Y=3000
# ---- K: UpdatePosition + diagnostics
k=keyev("K",[0,Y]); ss=subsys([0,Y+200]); gid=add(node_type="VariableGet",variable_name="HookRegId",position=[0,Y+300])
li,lp=lit([0,Y+400]); gl=add(node_type="CallFunction",function_name="K2_GetActorLocation",target_class="Actor",position=[230,Y+400])
gof=add(node_type="VariableGet",variable_name="HookPtOffset",position=[230,Y+500]); ad=add(node_type="CallFunction",function_name="Add_VectorVector",target_class="KismetMathLibrary",position=[460,Y+450])
up=add(node_type="CallFunction",function_name="UpdatePosition",target_class="SBTransitDestinationSubsystem",position=[700,Y])
con(k,"Pressed",up,"execute"); con(ss,"ReturnValue",up,"self"); con(gid,"HookRegId",up,"InId"); con(li,lp,gl,"self"); con(gl,"ReturnValue",ad,"A"); con(gof,"HookPtOffset",ad,"B"); con(ad,"ReturnValue",up,"InNewLocation")
gd=add(node_type="CallFunction",function_name="GetData",target_class="SBTransitDestinationSubsystem",position=[950,Y+300])
br=add(node_type="BreakStruct",struct_type="SBTransitDestinationData",position=[1180,Y+300])
cv=add(node_type="CallFunction",function_name="Conv_VectorToString",target_class="KismetStringLibrary",position=[1410,Y+300])
p1=printstr([1650,Y],"pos"); con(up,"then",p1,"execute"); con(ss,"ReturnValue",gd,"self"); con(gid,"HookRegId",gd,"InId"); con(gd,"OutData",br,"SBTransitDestinationData"); con(br,"Location",cv,"InVec"); con(cv,"ReturnValue",p1,"InString")
fn=add(node_type="CallFunction",function_name="FindNearest",target_class="SBTransitDestinationSubsystem",position=[1900,Y+300])
bq("set_pin_default",dict(node_id=fn,pin_name="InMaxRadius",value="300"))
cb=add(node_type="CallFunction",function_name="Conv_BoolToString",target_class="KismetStringLibrary",position=[2130,Y+300])
p2=printstr([2350,Y],"find"); con(p1,"then",p2,"execute"); con(ss,"ReturnValue",fn,"self"); con(ad,"ReturnValue",fn,"InLocation"); con(br,"Type",fn,"InType"); con(fn,"ReturnValue",cb,"InBool"); con(cb,"ReturnValue",p2,"InString")
# ---- L: Unregister + Register with new data
l=keyev("L",[0,Y+900]); ss2=subsys([0,Y+1100]); gid2=add(node_type="VariableGet",variable_name="HookRegId",position=[0,Y+1200])
gd2=add(node_type="CallFunction",function_name="GetData",target_class="SBTransitDestinationSubsystem",position=[230,Y+1100])
br2=add(node_type="BreakStruct",struct_type="SBTransitDestinationData",position=[460,Y+1100])
mk=bq("add_node",dict(node_type="MakeStruct",struct_type="SBTransitDestinationData",position=[900,Y+1100])); mkid=mk["id"]; fields=[p["name"] for p in mk["pins"] if p["name"]!="SBTransitDestinationData"]
li2,lp2=lit([230,Y+1500]); gl2=add(node_type="CallFunction",function_name="K2_GetActorLocation",target_class="Actor",position=[460,Y+1500])
gof2=add(node_type="VariableGet",variable_name="HookPtOffset",position=[460,Y+1600]); ad2=add(node_type="CallFunction",function_name="Add_VectorVector",target_class="KismetMathLibrary",position=[690,Y+1550])
con(li2,lp2,gl2,"self"); con(gl2,"ReturnValue",ad2,"A"); con(gof2,"HookPtOffset",ad2,"B")
con(ss2,"ReturnValue",gd2,"self"); con(gid2,"HookRegId",gd2,"InId"); con(gd2,"OutData",br2,"SBTransitDestinationData")
for f in fields:
    if f=="Location": con(ad2,"ReturnValue",mkid,f)
    else: con(br2,f,mkid,f)
un=add(node_type="CallFunction",function_name="Unregister",target_class="SBTransitDestinationSubsystem",position=[1200,Y+900])
rg=add(node_type="CallFunction",function_name="Register",target_class="SBTransitDestinationSubsystem",position=[1450,Y+900])
sid=add(node_type="VariableSet",variable_name="HookRegId",position=[1700,Y+900])
cg=add(node_type="CallFunction",function_name="Conv_GuidToString",target_class="KismetGuidLibrary",position=[1700,Y+1050]) if False else None
p3=printstr([1950,Y+900],"reg"); 
con(l,"Pressed",un,"execute"); con(ss2,"ReturnValue",un,"self"); con(gid2,"HookRegId",un,"InId")
con(un,"then",rg,"execute"); con(ss2,"ReturnValue",rg,"self"); con(mkid,"SBTransitDestinationData",rg,"InData")
con(rg,"then",sid,"execute"); con(rg,"ReturnValue",sid,"HookRegId"); con(sid,"then",p3,"execute")
bq("set_pin_default",dict(node_id=p3,pin_name="InString",value="REREGISTERED"))
c=bq("compile_blueprint",{}); print("COMPILE",{k:c.get(k) for k in ("success","error_count","errors")})
