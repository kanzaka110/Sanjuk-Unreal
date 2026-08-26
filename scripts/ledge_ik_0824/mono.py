import json, urllib.request
URL="http://localhost:9316/mcp"
def call(tool, action, params, timeout=300):
    body={"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":tool,"arguments":{"action":action,"params":params}}}
    req=urllib.request.Request(URL,json.dumps(body).encode(),{"Content-Type":"application/json"})
    r=json.load(urllib.request.urlopen(req,timeout=timeout)); res=r["result"]; txt=res["content"][0]["text"]
    if res.get("isError"): raise RuntimeError(action+": "+txt[:500])
    return json.loads(txt)
ed=lambda a,p: call("editor_query",a,p)
an=lambda a,p: call("animation_query",a,p)
PC={"class_name":"PC_01"}
def pcall(fn,args=None,anim=False,comp=None):
    p=dict(PC,function=fn); 
    if args: p["args"]=args
    if anim: p["anim_instance"]=True
    if comp: p["component_name"]=comp
    return ed("pie_call_function",p)
def pget(props,anim=False,comp=None):
    p=dict(PC,properties=props)
    if anim: p["anim_instance"]=True
    if comp: p["component_name"]=comp
    return ed("pie_get_object_properties",p)
