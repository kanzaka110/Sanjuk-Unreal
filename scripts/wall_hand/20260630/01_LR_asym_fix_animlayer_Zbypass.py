import urllib.request,json
L="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK";U="http://localhost:9316/mcp"
def call(action,**p):
    p["asset_path"]=L
    body=json.dumps({"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":"blueprint_query","arguments":{"action":action,"params":p}}}).encode()
    r=urllib.request.urlopen(urllib.request.Request(U,body,{"Content-Type":"application/json"}),timeout=30);d=json.loads(r.read());res=d.get("result",{})
    return ("ERR" if res.get("isError") else "OK"), res.get("content",[{}])[0].get("text","")[:80]
print("disc CF_23.Z:",call("disconnect_pins",graph_name="EventGraph",node_id="K2Node_CallFunction_23",pin_name="Z"))
print("conn CF_20.Z -> CF_23.Z:",call("connect_pins",graph_name="EventGraph",source_node="K2Node_CallFunction_20",source_pin="Z",target_node="K2Node_CallFunction_23",target_pin="Z"))
