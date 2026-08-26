import json, urllib.request, sys
URL="http://localhost:9316/mcp"
BP="/Game/Developers/SHIFTUP/GameDesign/System/Users/JHJ/Map/InteractionTest/JHJ_InteractionTest_WP"
INTERVAL=sys.argv[1] if len(sys.argv)>1 else "0.5"
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
# existing timer/custom event? remove if present
for nid,n in list(nodes.items()):
    if n["class"]=="K2Node_CustomEvent" and "HookRefresh" in json.dumps(n): bq("remove_node",dict(node_id=nid)); print("rm old event")
# find literal per hookshot via SetActorLocation self pins
lits={}
for nid,n in nodes.items():
    if n["class"]=="K2Node_CallFunction" and "SetActorLocation" in json.dumps(n):
        c=[p.get("connected_to") for p in n["pins"] if p["name"]=="self"][0]
        if c:
            ln,lp=c[0].split("."); 
            if "Hookshot" in lp: lits[lp]=(ln,lp)
print(lits)
MAP={"InAir12":"BP_EM_Hookshot_InAir12","Swing4":"BP_EM_Hookshot_Swing4","Swing5":"BP_EM_Hookshot_Swing5"}
# end of BeginPlay chain: last Set HookPtOffset_Swing5
end=[nid for nid,n in nodes.items() if n["class"]=="K2Node_VariableSet" and "HookPtOffset_Swing5" in json.dumps(n) and any(p.get("connected_to") for p in n["pins"] if p["name"]=="execute")]
print("end",end)
Y=2200
ev=add(node_type="CustomEvent",event_name="HookRefresh",position=[0,Y]); prev,pp=ev,"then"; x=350
for k,lab in MAP.items():
    ln,lp=lits[lab]
    mv=add(node_type="CallFunction",function_name="MoveHookPoint",position=[x,Y]); gi=add(node_type="VariableGet",variable_name="HookRegId_"+k,position=[x-230,Y+150]); go=add(node_type="VariableGet",variable_name="HookPtOffset_"+k,position=[x-230,Y+220]); st=add(node_type="VariableSet",variable_name="HookRegId_"+k,position=[x+300,Y])
    con(prev,pp,mv,"execute"); con(gi,"HookRegId_"+k,mv,"Id"); con(ln,lp,mv,"HookActor"); con(go,"HookPtOffset_"+k,mv,"Offset"); con(mv,"then",st,"execute"); con(mv,"NewId",st,"HookRegId_"+k)
    prev,pp=st,"then"; x+=650
tm=add(node_type="CallFunction",function_name="K2_SetTimer",target_class="KismetSystemLibrary",position=[nodes[end[0]]["pos"][0]+350,nodes[end[0]]["pos"][1]])
for k,v in [("FunctionName","HookRefresh"),("Time",INTERVAL),("bLooping","true")]: bq("set_pin_default",dict(node_id=tm,pin_name=k,value=v))
slf=add(node_type="Self",position=[nodes[end[0]]["pos"][0]+120,nodes[end[0]]["pos"][1]+150])
con(end[0],"then",tm,"execute"); con(slf,"self",tm,"Object")
c=bq("compile_blueprint",{}); print("COMPILE",{k:c.get(k) for k in ("success","error_count","warning_count","errors")})
