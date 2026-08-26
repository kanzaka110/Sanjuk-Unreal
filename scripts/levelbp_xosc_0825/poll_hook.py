import json, urllib.request, time, sys
URL="http://localhost:9316/mcp"
def call(tool, action, params, timeout=60):
    body={"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":tool,"arguments":{"action":action,"params":params}}}
    req=urllib.request.Request(URL,json.dumps(body).encode(),{"Content-Type":"application/json"})
    r=json.load(urllib.request.urlopen(req,timeout=timeout)); res=r["result"]; txt=res["content"][0]["text"]
    if res.get("isError"): raise RuntimeError(action+": "+txt[:800])
    return json.loads(txt)
HOOK="BP_EM_Hookshot_InAir_C_UAID_30560F6BCAE568FB02_1136314272"
for i in range(int(sys.argv[1]) if len(sys.argv)>1 else 5):
    try:
        a=call("editor_query","pie_call_function",{"object_name":HOOK,"function":"K2_GetActorLocation"}).get("return_value")
        r=call("editor_query","pie_call_function",{"class_name":"JHJ_InteractionTest_WP_C","function":"DbgHookLoc","args":{"HookActor":HOOK}})
        print(i,"actor",a,"| reg",r.get("return_value") or r.get("outputs") or r)
    except Exception as e: print(i,"ERR",str(e)[:300]); 
    time.sleep(0.25)
