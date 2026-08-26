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
    try: bq("connect_pins",dict(source_node=s,source_pin=sp,target_node=t,target_pin=tp)); print("OK",sp,"->",t,tp)
    except Exception as e: print("FAIL",sp,"->",t,tp,e)
# custom event + ResetActor
ev=add(node_type="CustomEvent",event_name="ResetHookPoint",position=[0,1400])
rs=add(node_type="CallFunction",function_name="ResetActor",target_class="SBZoneEnvActor",position=[450,1400])
li=add(node_type="K2Node_Literal",position=[220,1550])
bq("set_node_property",dict(node_id=li,property_name="ObjectRef",value=LVL+HOOK)); bq("refresh_node",dict(node_id=li))
lp=[p["name"] for p in bq("get_node_details",dict(node_id=li))["pins"]][0]
con(ev,"then",rs,"execute"); con(li,lp,rs,"self")
# timer after BeginPlay chain (last = K2Node_VariableSet_2)
tm=add(node_type="CallFunction",function_name="K2_SetTimerByFunctionName",target_class="KismetSystemLibrary",position=[1800,0])
bq("set_pin_default",dict(node_id=tm,pin_name="FunctionName",value="ResetHookPoint"))
bq("set_pin_default",dict(node_id=tm,pin_name="Time",value="0.2"))
bq("set_pin_default",dict(node_id=tm,pin_name="bLooping",value="true"))
slf=add(node_type="Self",position=[1570,150])
sp=[p["name"] for p in bq("get_node_details",dict(node_id=slf))["pins"]][0]
con("K2Node_VariableSet_2","then",tm,"execute"); con(slf,sp,tm,"Object")
c=bq("compile_blueprint",{}); print("COMPILE",{k:c.get(k) for k in ("success","error_count","warning_count","errors","warnings")})
