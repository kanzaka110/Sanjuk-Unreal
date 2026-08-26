# PC_01_ABP: GetLedgeIKDebugMirror 디버그 함수 배선 (레이어 LedgeState 미러)
import json, urllib.request, sys
URL="http://localhost:9316/mcp"
ABP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
FN="GetLedgeIKDebugMirror"
def call(tool, action, params, timeout=300):
    body={"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":tool,"arguments":{"action":action,"params":params}}}
    req=urllib.request.Request(URL,json.dumps(body).encode(),{"Content-Type":"application/json"})
    r=json.load(urllib.request.urlopen(req,timeout=timeout)); res=r["result"]; txt=res["content"][0]["text"]
    if res.get("isError"): raise RuntimeError(action+": "+txt[:400])
    return json.loads(txt)
bq=lambda a,p: call("blueprint_query",a,p)

outs=[("bLayerFound","bool"),("HandL","struct:Vector"),("HandR","struct:Vector"),("FootL","struct:Vector"),("FootR","struct:Vector"),
      ("HandAlphaL","double"),("HandAlphaR","double"),("FootAlphaL","double"),("FootAlphaR","double"),("DangleAlpha","double"),("MeshToWorld","struct:Transform")]
print(bq("set_function_params",{"asset_path":ABP,"function_name":FN,"outputs":[{"name":n,"type":t} for n,t in outs]}))
g=bq("get_graph_data",{"asset_path":ABP,"graph_name":FN})
ids={}
for n in g["nodes"]:
    c=n.get("class",""); t=n.get("title","")
    if "FunctionEntry" in c: ids["entry"]=n["id"]
    elif "FunctionResult" in c: ids["ret"]=n["id"]
    elif "DynamicCast" in c: ids["cast"]=n["id"]
    elif "CallFunction" in c and "GetLinkedAnimLayerInstanceByClass" in json.dumps(n): ids["getl"]=n["id"]
    elif "CallFunction" in c and "LedgeState" in json.dumps(n): ids["ls"]=n["id"]
print(ids)
for n in g["nodes"]:
    if n["id"] in (ids.get("ret"),ids.get("cast")): print(n["id"],[p["name"] for p in n["pins"]])
# 클래스 핀 기본값
print(bq("set_pin_default",{"asset_path":ABP,"node_id":ids["getl"],"pin_name":"InClass","value":"/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge.PC_01_AnimLayer_Ledge_C"}))
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
    try: r=bq("connect_pins",{"asset_path":ABP,"source_node":s,"source_pin":sp,"target_node":t,"target_pin":tp}); print("OK",sp,"->",tp,r.get("success",r))
    except Exception as e: print("FAIL",sp,"->",tp,e)
print(bq("set_pin_default",{"asset_path":ABP,"node_id":ids["ret"],"pin_name":"bLayerFound","value":"true"}))
