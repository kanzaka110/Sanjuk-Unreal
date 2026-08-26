import json, urllib.request
URL="http://localhost:9316/mcp"
ABP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"; FN="GetLedgeIKDebugMirror"
LAYER_C="/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge.PC_01_AnimLayer_Ledge_C"
def call(tool, action, params, timeout=300):
    body={"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":tool,"arguments":{"action":action,"params":params}}}
    req=urllib.request.Request(URL,json.dumps(body).encode(),{"Content-Type":"application/json"})
    r=json.load(urllib.request.urlopen(req,timeout=timeout)); res=r["result"]; txt=res["content"][0]["text"]
    if res.get("isError"): raise RuntimeError(action+": "+txt[:400])
    return json.loads(txt)
bq=lambda a,p: call("blueprint_query",a,p)
def graph():
    g=bq("get_graph_data",{"asset_path":ABP,"graph_name":FN}); ids={}
    for n in g["nodes"]:
        c=n.get("class",""); s=json.dumps(n)
        if "FunctionEntry" in c: ids["entry"]=n["id"]
        elif "FunctionResult" in c: ids["ret"]=n["id"]
        elif "DynamicCast" in c: ids["cast"]=n["id"]
        elif "CallFunction" in c and "GetLinkedAnimLayerInstanceByClass" in s: ids["getl"]=n["id"]; ids["getl_pins"]=[p["name"] for p in n["pins"]]
        elif "CallFunction" in c and "LedgeState" in s: ids["ls"]=n["id"]
    return ids
ids=graph(); print(ids)
if "InClass" not in ids.get("getl_pins",[]):
    try: print(bq("refresh_node",{"asset_path":ABP,"graph_name":FN,"node_id":ids["getl"]}))
    except Exception as e: print("refresh fail",e)
    ids=graph(); print("after refresh",ids.get("getl_pins"))
if "InClass" not in ids.get("getl_pins",[]):
    print(bq("remove_node",{"asset_path":ABP,"graph_name":FN,"node_id":ids["getl"]}))
    r=bq("add_node",{"asset_path":ABP,"graph_name":FN,"node_type":"CallFunction","function_name":"GetLinkedAnimLayerInstanceByClass","target_class":"AnimInstance","position":[300,0]})
    print("readded",r["id"],[p["name"] for p in r["pins"]]); ids=graph()
print(bq("set_pin_default",{"asset_path":ABP,"graph_name":FN,"node_id":ids["getl"],"pin_name":"InClass","value":LAYER_C}))
con=[
 (ids["entry"],"then",ids["cast"],"execute"),
 (ids["getl"],"ReturnValue",ids["cast"],"Object"),
 (ids["cast"],"then",ids["ls"],"execute"),
 (ids["cast"],"AsPC 01 Anim Layer Ledge",ids["ls"],"self"),
 (ids["ls"],"then",ids["ret"],"execute"),
 (ids["cast"],"CastFailed",ids["ret"],"execute"),
 (ids["ls"],"LedgeHandWorldPredL",ids["ret"],"HandL"),
 (ids["ls"],"LedgeHandWorldPredR",ids["ret"],"HandR"),
 (ids["ls"],"LedgeHandIKAlphaL",ids["ret"],"HandAlphaL"),
 (ids["ls"],"LedgeHandIKAlphaR",ids["ret"],"HandAlphaR"),
 (ids["ls"],"LedgeFootIKAlphaL",ids["ret"],"FootAlphaL"),
 (ids["ls"],"LedgeFootIKAlphaR",ids["ret"],"FootAlphaR"),
 (ids["ls"],"LedgeDangleAlpha",ids["ret"],"DangleAlpha"),
 (ids["ls"],"LedgeMeshToWorldOut",ids["ret"],"MeshToWorld"),
]
for s,sp,t,tp in con:
    try: r=bq("connect_pins",{"asset_path":ABP,"graph_name":FN,"source_node":s,"source_pin":sp,"target_node":t,"target_pin":tp}); print("OK",sp,"->",tp,r.get("success",r))
    except Exception as e: print("FAIL",sp,"->",tp,e)
print(bq("set_pin_default",{"asset_path":ABP,"graph_name":FN,"node_id":ids["ret"],"pin_name":"bLayerFound","value":"true"}))
c=bq("compile_blueprint",{"asset_path":ABP}); print("COMPILE",{k:c.get(k) for k in ("success","errors","warnings","error_count","warning_count","num_errors","num_warnings")})
