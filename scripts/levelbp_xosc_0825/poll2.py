import json, urllib.request, time
URL="http://localhost:9316/mcp"
def call(tool, action, params, timeout=60):
    body={"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":tool,"arguments":{"action":action,"params":params}}}
    req=urllib.request.Request(URL,json.dumps(body).encode(),{"Content-Type":"application/json"})
    r=json.load(urllib.request.urlopen(req,timeout=timeout)); res=r["result"]; txt=res["content"][0]["text"]
    if res.get("isError"): raise RuntimeError(action+": "+txt[:800])
    return json.loads(txt)
def loc(cn,comp=None):
    p={"class_name":cn,"function":"K2_GetComponentLocation" if comp else "K2_GetActorLocation"}
    if comp: p["component_name"]=comp
    r=call("editor_query","pie_call_function",p); return r.get("return_value",r)
for i in range(4):
    out={}
    for k,c in [("actor",None),("HookAnchor","HookAnchor"),("HookDestination","HookDestination"),("Cube","Cube"),("Root","RootComponent")]:
        try: out[k]=loc("BP_EM_Hookshot_InAir_C",c)
        except Exception as e: out[k]="ERR "+str(e)[:120]
    try: out["Cube67"]=loc("StaticMeshActor")
    except Exception as e: out["Cube67"]="ERR "+str(e)[:120]
    print(i,json.dumps(out)[:900]); time.sleep(1.2)
