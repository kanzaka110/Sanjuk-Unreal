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
print(bq("refresh_node",dict(node_id="K2Node_Timeline_0")))
print([p["name"] for p in bq("get_node_details",dict(node_id="K2Node_Timeline_0"))["pins"]])
print(bq("connect_pins",dict(source_node="K2Node_Timeline_0",source_pin="Alpha",target_node="K2Node_CallFunction_4",target_pin="A")))
print(bq("remove_variable",dict(name="XOscPeriod")))
c=bq("compile_blueprint",{}); print("COMPILE",{k:c.get(k) for k in ("success","status","error_count","warning_count","errors","warnings")})
f=bq("get_execution_flow",{}); print(json.dumps(f)[:1500])
