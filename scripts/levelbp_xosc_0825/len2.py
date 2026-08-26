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
try: print(bq("set_node_property",dict(node_id="K2Node_Timeline_0",property_name="TimelineLength",value=2.0)))
except Exception as e: print("np fail",e)
L=bq("get_timeline_data",dict(timeline_name="XOscTimeline"))["timelines"][0]["length"]; print("len",L)
if L!=2:
    keys=[{"time":t,"value":v,"interp_mode":"cubic"} for t,v in [(0,0),(1.25,1),(2.5,0),(3.75,1),(5,0)]]
    print(bq("set_timeline_keys",dict(timeline_name="XOscTimeline",track_name="Alpha",keys=keys)))
c=bq("compile_blueprint",{}); print("COMPILE",c["success"],c["error_count"])
