import json, urllib.request, sys
URL="http://localhost:9316/mcp"
MAP="/Game/Developers/SHIFTUP/GameDesign/System/Users/JHJ/Map/InteractionTest/JHJ_InteractionTest_WP"
BP=MAP  # level blueprint resolves from map path
LVL=MAP+".JHJ_InteractionTest_WP:PersistentLevel."
ACTORS=[("Cube67","StaticMeshActor_UAID_30560F6BCAE568FB02_1136276269"),
        ("Cube66","StaticMeshActor_UAID_30560F6BCAE568FB02_1136313271"),
        ("Hookshot12","BP_EM_Hookshot_InAir_C_UAID_30560F6BCAE568FB02_1136314272")]
def call(tool, action, params, timeout=120):
    body={"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":tool,"arguments":{"action":action,"params":params}}}
    req=urllib.request.Request(URL,json.dumps(body).encode(),{"Content-Type":"application/json"})
    r=json.load(urllib.request.urlopen(req,timeout=timeout)); res=r["result"]; txt=res["content"][0]["text"]
    if res.get("isError"): raise RuntimeError(action+": "+txt[:600])
    return json.loads(txt)
bq=lambda a,p: call("blueprint_query",a,dict(asset_path=BP,**p))
def add(**k):
    r=bq("add_node",k); return r["id"],[p["name"] for p in r.get("pins",[])]
def con(s,sp,t,tp):
    try: bq("connect_pins",dict(source_node=s,source_pin=sp,target_node=t,target_pin=tp)); print("OK",s,sp,"->",t,tp)
    except Exception as e: print("FAIL",s,sp,"->",t,tp,e)
def lit(objname,pos):
    nid,_=add(node_type="K2Node_Literal",position=pos)
    bq("set_node_property",dict(node_id=nid,property_name="ObjectRef",value=LVL+objname))
    r=bq("refresh_node",dict(node_id=nid))
    pins=[p["name"] for p in bq("get_node_details",dict(node_id=nid)).get("pins",[])]
    print("LIT",nid,pins); return nid,pins

# variables
for name,typ,dv in [("XOscAmplitude","float",200.0),("XOscPeriod","float",2.0)]+[("StartLoc_"+a,"vector",None) for a,_ in ACTORS]:
    try: print(bq("add_variable",dict(name=name,type=typ)))
    except Exception as e: print("var",name,e)
    if dv is not None:
        try: print(bq("set_variable_defaults",dict(name=name,default_value=dv)))
        except Exception as e: print("def",name,e)

# timeline
tl=bq("add_timeline",dict(timeline_name="XOscTimeline",auto_play=True,loop=True,position=[0,700])); print("TL",json.dumps(tl)[:400])
tlid=tl.get("node_id") or tl.get("id")
print(bq("add_timeline_track",dict(timeline_name="XOscTimeline",track_name="Alpha")))
print(bq("set_timeline_keys",dict(timeline_name="XOscTimeline",track_name="Alpha",keys=[{"time":0,"value":0,"interp_mode":"cubic"},{"time":1,"value":1,"interp_mode":"cubic"},{"time":2,"value":0,"interp_mode":"cubic"}])))
tlpins=[p["name"] for p in bq("get_node_details",dict(node_id=tlid)).get("pins",[])]; print("TLPINS",tlpins)

# BeginPlay row: cache start locations
bp="K2Node_Event_0"; bq("set_node_position",dict(node_id=bp,position=[0,0]))
prev,pp=bp,"then"
for i,(a,obj) in enumerate(ACTORS):
    x=450+i*450
    sv,_=add(node_type="VariableSet",variable_name="StartLoc_"+a,position=[x,0])
    gl,_=add(node_type="CallFunction",function_name="K2_GetActorLocation",target_class="Actor",position=[x-230,150])
    li,lp=lit(obj,[x-460,150])
    con(prev,pp,sv,"execute"); prev,pp=sv,"then"
    con(li,lp[0],gl,"self"); con(gl,"ReturnValue",sv,"StartLoc_"+a)

# Update row
mv,_=add(node_type="CallFunction",function_name="Multiply_VectorFloat",target_class="KismetMathLibrary",position=[400,950])
bq("set_pin_default",dict(node_id=mv,pin_name="A",value="1,0,0"))
md,_=add(node_type="CallFunction",function_name="Multiply_DoubleDouble",target_class="KismetMathLibrary",position=[170,1000])
ga,_=add(node_type="VariableGet",variable_name="XOscAmplitude",position=[-60,1050])
con(tlid,"Alpha",md,"A"); con(ga,"XOscAmplitude",md,"B"); con(md,"ReturnValue",mv,"B")
prev,pp=tlid,"Update"
for i,(a,obj) in enumerate(ACTORS):
    x=900+i*450
    sl,_=add(node_type="CallFunction",function_name="K2_SetActorLocation",target_class="Actor",position=[x,700])
    bq("set_pin_default",dict(node_id=sl,pin_name="bTeleport",value="true"))
    av,_=add(node_type="CallFunction",function_name="Add_VectorVector",target_class="KismetMathLibrary",position=[x-230,850])
    gv,_=add(node_type="VariableGet",variable_name="StartLoc_"+a,position=[x-460,850])
    li,lp=lit(obj,[x-460,780])
    con(prev,pp,sl,"execute"); prev,pp=sl,"then"
    con(li,lp[0],sl,"self"); con(gv,"StartLoc_"+a,av,"A"); con(mv,"ReturnValue",av,"B"); con(av,"ReturnValue",sl,"NewLocation")

c=bq("compile_blueprint",{}); print("COMPILE",json.dumps(c)[:1500])
