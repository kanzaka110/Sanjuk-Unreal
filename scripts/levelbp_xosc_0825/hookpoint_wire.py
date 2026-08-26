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
def add(**k): r=bq("add_node",k); return r["id"]
def con(s,sp,t,tp):
    try: bq("connect_pins",dict(source_node=s,source_pin=sp,target_node=t,target_pin=tp)); print("OK",s,sp,"->",t,tp)
    except Exception as e: print("FAIL",s,sp,"->",t,tp,str(e)[:160])
nodes={n["id"]:n for n in bq("get_graph_data",{})["nodes"]}
def selfsrc(nid):  # literal node id + pin for SetActorLocation node
    c=[p["connected_to"] for p in nodes[nid]["pins"] if p["name"]=="self"][0][0]; return c.split(".")[0],c.split(".")[1]
def newloc(nid): return [p["connected_to"][0] for p in nodes[nid]["pins"] if p["name"]=="NewLocation"][0].split(".")
ACT={"InAir12":("K2Node_CallFunction_19","StartLoc_Hookshot12"),"Swing4":("K2Node_CallFunction_21","StartLoc_Hookshot_Swing4"),"Swing5":("K2Node_CallFunction_9","StartLoc_Hookshot_Swing5")}
for old in ("HookRegId","HookPtOffset"):
    try: bq("remove_variable",dict(name=old))
    except Exception as e: print("rmvar",old,str(e)[:80])
for k in ACT:
    bq("add_variable",dict(name="HookRegId_"+k,type="struct:Guid")); bq("add_variable",dict(name="HookPtOffset_"+k,type="struct:Vector"))
# --- restore then_1: StartLoc for Cube68 / Swing4 / Swing5
try: bq("remove_node",dict(node_id="K2Node_Knot_3"))
except Exception as e: print("knot",str(e)[:80])
prev,pp="K2Node_ExecutionSequence_0","then_1"; y=400; x=450
for sl,var in [("K2Node_CallFunction_5","StartLoc_Cube68"),("K2Node_CallFunction_21","StartLoc_Hookshot_Swing4"),("K2Node_CallFunction_9","StartLoc_Hookshot_Swing5")]:
    li,lp=selfsrc(sl); sv=add(node_type="VariableSet",variable_name=var,position=[x,y]); gl=add(node_type="CallFunction",function_name="K2_GetActorLocation",target_class="Actor",position=[x-230,y+150])
    con(prev,pp,sv,"execute"); con(li,lp,gl,"self"); con(gl,"ReturnValue",sv,var); prev,pp=sv,"then"; x+=450
# --- Init chain after then_1 chain
for k,(sl,_) in ACT.items():
    li,lp=selfsrc(sl)
    init=add(node_type="CallFunction",function_name="InitHookPoint",position=[x,y]); s1=add(node_type="VariableSet",variable_name="HookRegId_"+k,position=[x+300,y]); s2=add(node_type="VariableSet",variable_name="HookPtOffset_"+k,position=[x+600,y])
    con(prev,pp,init,"execute"); con(li,lp,init,"HookActor"); con(init,"then",s1,"execute"); con(init,"Id",s1,"HookRegId_"+k); con(s1,"then",s2,"execute"); con(init,"Offset",s2,"HookPtOffset_"+k)
    prev,pp=s2,"then"; x+=950
# --- Update chains: after each hookshot SetActorLocation
for k,(sl,_) in ACT.items():
    li,lp=selfsrc(sl); pos=nodes[sl].get("pos",[0,0]); x0,y0=pos[0]+260,pos[1]
    nxt=[p.get("connected_to") for p in nodes[sl]["pins"] if p["name"]=="then"][0]
    mv=add(node_type="CallFunction",function_name="MoveHookPoint",position=[x0,y0+220]); gi=add(node_type="VariableGet",variable_name="HookRegId_"+k,position=[x0-230,y0+370]); go=add(node_type="VariableGet",variable_name="HookPtOffset_"+k,position=[x0-230,y0+440])
    st=add(node_type="VariableSet",variable_name="HookRegId_"+k,position=[x0+300,y0+220])
    bq("disconnect_pins",dict(node_id=sl,pin_name="then"))
    con(sl,"then",mv,"execute"); con(gi,"HookRegId_"+k,mv,"Id"); con(li,lp,mv,"HookActor"); con(go,"HookPtOffset_"+k,mv,"Offset")
    con(mv,"then",st,"execute"); con(mv,"NewId",st,"HookRegId_"+k)
    if nxt: n2,p2=nxt[0].split("."); con(st,"then",n2,p2)
c=bq("compile_blueprint",{}); print("COMPILE",{k:c.get(k) for k in ("success","error_count","errors","warning_count")})
