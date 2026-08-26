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
# cleanup partial from previous run: CustomEvent HookRefresh + unconnected MoveHookPoint/timer nodes
for nid,n in list(nodes.items()):
    s=json.dumps(n)
    if (n["class"]=="K2Node_CustomEvent" and "HookRefresh" in s) or (n["class"]=="K2Node_CallFunction" and ("MoveHookPoint" in s or "K2_SetTimer" in s) and not any(p.get("connected_to") for p in n["pins"] if p["name"]=="HookActor" or p["name"]=="Object")) or (n["class"]=="K2Node_Self"):
        bq("remove_node",dict(node_id=nid)); print("rm",nid,n["class"])
nodes={n["id"]:n for n in bq("get_graph_data",{})["nodes"]}
mvs=[]
for nid,n in nodes.items():
    if n["class"]=="K2Node_CallFunction" and "MoveHookPoint" in json.dumps(n):
        st=[p.get("connected_to") for p in n["pins"] if p["name"]=="then"][0]
        mvs.append((nid, st[0].split(".")[0] if st else None)); 
print("mv nodes",mvs)
assert len(mvs)==3 and all(s for _,s in mvs)
end=[nid for nid,n in nodes.items() if n["class"]=="K2Node_VariableSet" and "HookPtOffset_Swing5" in json.dumps(n) and any(p.get("connected_to") for p in n["pins"] if p["name"]=="execute")][0]
Y=2200
ev=add(node_type="CustomEvent",event_name="HookRefresh",position=[0,Y]); prev,pp=ev,"then"; x=350
for mv,st in mvs:
    bq("set_node_position",dict(node_id=mv,position=[x,Y])); bq("set_node_position",dict(node_id=st,position=[x+300,Y]))
    bq("disconnect_pins",dict(node_id=st,pin_name="then"))
    con(prev,pp,mv,"execute"); prev,pp=st,"then"; x+=650
tm=add(node_type="CallFunction",function_name="K2_SetTimer",target_class="KismetSystemLibrary",position=[nodes[end]["pos"][0]+350,nodes[end]["pos"][1]])
for k,v in [("FunctionName","HookRefresh"),("Time",INTERVAL),("bLooping","true")]: bq("set_pin_default",dict(node_id=tm,pin_name=k,value=v))
slf=add(node_type="Self",position=[nodes[end]["pos"][0]+120,nodes[end]["pos"][1]+150])
con(end,"then",tm,"execute"); con(slf,"self",tm,"Object")
c=bq("compile_blueprint",{}); print("COMPILE",{k:c.get(k) for k in ("success","error_count","warning_count","errors")})
