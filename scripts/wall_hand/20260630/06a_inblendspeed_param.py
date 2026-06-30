import urllib.request,json
A="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP";U="http://localhost:9316/mcp"
def bq(action,**p):
    p["asset_path"]=A
    body=json.dumps({"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":"blueprint_query","arguments":{"action":action,"params":p}}}).encode()
    r=urllib.request.urlopen(urllib.request.Request(U,body,{"Content-Type":"application/json"}),timeout=30)
    d=json.loads(r.read());res=d.get("result",{})
    return ("ERR" if res.get("isError") else "OK"),res.get("content",[{}])[0].get("text","")[:120]
print("Data += InBlendSpeed:",bq("set_function_params",function_name="SetWallHandData",inputs=[{"name":"InBlendSpeed","type":"float"}]))
print("Front += InBlendSpeed:",bq("set_function_params",function_name="SetWallHandFront",inputs=[{"name":"InBlendSpeed","type":"float"}]))
