import json, urllib.request, sys
URL="http://localhost:9316/mcp"
BP="/Game/Developers/SHIFTUP/GameDesign/System/Users/JHJ/Map/InteractionTest/JHJ_InteractionTest_WP"
def call(tool, action, params, timeout=120):
    body={"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":tool,"arguments":{"action":action,"params":params}}}
    req=urllib.request.Request(URL,json.dumps(body).encode(),{"Content-Type":"application/json"})
    r=json.load(urllib.request.urlopen(req,timeout=timeout)); res=r["result"]; txt=res["content"][0]["text"]
    if res.get("isError"): raise RuntimeError(action+": "+txt[:600])
    return json.loads(txt)
bq=lambda a,p: call("blueprint_query",a,dict(asset_path=BP,**p))
add=lambda **k: bq("add_node",k)["id"]
def con(s,sp,t,tp):
    try: bq("connect_pins",dict(source_node=s,source_pin=sp,target_node=t,target_pin=tp)); print("OK",sp,"->",t,tp)
    except Exception as e: print("FAIL",s,sp,"->",t,tp,str(e)[:160])
nodes={n["id"]:n for n in bq("get_graph_data",{})["nodes"]}
lit={}
for nid,n in nodes.items():
    if n["class"]=="K2Node_Literal":
        lab=n.get("title","").split("\n")[0]; lit.setdefault(lab,(nid,[p["name"] for p in n["pins"] if p["direction"]=="output"][0]))
# BeginPlay then_0 chain end
seq=[nid for nid,n in nodes.items() if n["class"]=="K2Node_ExecutionSequence"][0]
cur=[p["connected_to"] for p in nodes[seq]["pins"] if p["name"]=="then_0"][0]; end=None
while cur:
    end=cur[0].split(".")[0]; cur=[p.get("connected_to") for p in nodes[end]["pins"] if p["name"]=="then" and p["direction"]=="output"][0]
print("end",end,nodes[end].get("title"))
pos=nodes[end].get("pos",[0,0])
tm=add(node_type="CallFunction",function_name="K2_SetTimer",target_class="KismetSystemLibrary",position=[pos[0]+350,pos[1]])
for k,v in [("FunctionName","ResetHookPoint"),("Time","0.2"),("bLooping","true")]: bq("set_pin_default",dict(node_id=tm,pin_name=k,value=v))
slf=add(node_type="Self",position=[pos[0]+120,pos[1]+150]); con(end,"then",tm,"execute"); con(slf,"self",tm,"Object")
Y=2900; ev=add(node_type="CustomEvent",event_name="ResetHookPoint",position=[0,Y]); prev,pp=ev,"then"; x=350
for lab in ["BP_EM_Hookshot_InAir12","BP_EM_Hookshot_Swing4","BP_EM_Hookshot_Swing5"]:
    ln,lp=lit[lab]
    gf=add(node_type="CallFunction",function_name="GetHookFeature",target_class="SBZoneEnvActor",position=[x-230,Y+150])
    gs=add(node_type="CallFunction",function_name="GetHookshotPointSettings",target_class="SBZoneEnvActorHookFeature",position=[x-230,Y+250])
    ss=add(node_type="CallFunction",function_name="SetHookshotPointSettings",target_class="SBZoneEnvActorHookFeature",position=[x,Y])
    gt=add(node_type="CallFunction",function_name="GetHookshotType",target_class="SBZoneEnvActorHookFeature",position=[x+120,Y+250])
    st=add(node_type="CallFunction",function_name="SetHookshotType",target_class="SBZoneEnvActorHookFeature",position=[x+350,Y])
    con(ln,lp,gf,"self"); con(gf,"ReturnValue",gs,"self"); con(gf,"ReturnValue",ss,"self"); con(gs,"ReturnValue",ss,"InSettings")
    con(gf,"ReturnValue",gt,"self"); con(gf,"ReturnValue",st,"self"); con(gt,"ReturnValue",st,"InHookshotType")
    con(prev,pp,ss,"execute"); con(ss,"then",st,"execute"); prev,pp=st,"then"; x+=750
c=bq("compile_blueprint",{}); print("COMPILE",{k:c.get(k) for k in ("success","error_count","warning_count","errors")})
