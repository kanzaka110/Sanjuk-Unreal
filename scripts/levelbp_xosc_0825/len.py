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
for path in ["Timelines[0].TimelineLength","Timelines.0.TimelineLength"]:
    try: print(path, bq("set_property_at_path",dict(path=path,value=2.0))); break
    except Exception as e: print("fail",path,e)
print(bq("get_timeline_data",dict(timeline_name="XOscTimeline"))["timelines"][0]["length"])
c=bq("compile_blueprint",{}); print("COMPILE",c["success"],c["error_count"])
