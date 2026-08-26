import json, urllib.request, time
URL="http://localhost:9316/mcp"
def call(tool, action, params, timeout=60):
    body={"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":tool,"arguments":{"action":action,"params":params}}}
    req=urllib.request.Request(URL,json.dumps(body).encode(),{"Content-Type":"application/json"})
    r=json.load(urllib.request.urlopen(req,timeout=timeout)); res=r["result"]; txt=res["content"][0]["text"]
    if res.get("isError"): raise RuntimeError(action+": "+txt[:800])
    return json.loads(txt)
for i in range(3):
    for cn in ["BP_EM_Hookshot_InAir_C","StaticMeshActor"]:
        try:
            r=call("editor_query","pie_get_object_properties",{"class_name":cn,"properties":["RootComponent.RelativeLocation","HookAnchor.RelativeLocation","HookAnchor.bAbsoluteLocation","HookDestination.RelativeLocation","Cube.RelativeLocation"]})
            print(i,cn,json.dumps(r,ensure_ascii=False)[:700])
        except Exception as e: print(i,cn,"ERR",str(e)[:300])
    time.sleep(1.5)
