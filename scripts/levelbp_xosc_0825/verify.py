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
bq("set_node_position",dict(node_id="K2Node_Event_1",position=[0,-300]))
for n in ["K2Node_Timeline_0","K2Node_CallFunction_5","K2Node_CallFunction_9","K2Node_CallFunction_3"]:
    d=bq("get_node_details",dict(node_id=n))
    print(n,[(p["name"],p.get("linked_to") or p.get("connections") or p.get("default_value")) for p in d["pins"] if p["name"] in("Update","then","execute","Alpha","A","B","NewLocation","self","bTeleport","bSweep")])
print(bq("get_variables",{}))
print(bq("get_timeline_data",dict(timeline_name="XOscTimeline")))
