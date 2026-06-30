import urllib.request,json
A="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP";U="http://localhost:9316/mcp"
def bq(action,**p):
    p["asset_path"]=A
    body=json.dumps({"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":"blueprint_query","arguments":{"action":action,"params":p}}}).encode()
    r=urllib.request.urlopen(urllib.request.Request(U,body,{"Content-Type":"application/json"}),timeout=30)
    d=json.loads(r.read());res=d.get("result",{})
    return "ERR("+res.get("content",[{}])[0].get("text","")[:60]+")" if res.get("isError") else "OK"

# 1) exec bypass: FunctionEntry.then -> VariableSet_0.execute (skip timer setters)
print("exec bypass:",bq("connect_pins",graph_name="SetWallHandData",source_node="K2Node_FunctionEntry_0",source_pin="then",target_node="K2Node_VariableSet_0",target_pin="execute"))

# 2) constant speed 15 on both VInterpTo
print("CF_2.InterpSpeed=15:",bq("set_pin_default",graph_name="SetWallHandData",node_id="K2Node_CallFunction_2",pin_name="InterpSpeed",value="15.000000"))
print("CF_4.InterpSpeed=15:",bq("set_pin_default",graph_name="SetWallHandFront",node_id="K2Node_CallFunction_4",pin_name="InterpSpeed",value="15.000000"))

# 3) delete timer nodes (Data) + WHBlendSpd getters
data_del=["K2Node_CallFunction_12","K2Node_CallFunction_13","K2Node_CallFunction_14","K2Node_CallFunction_15",
 "K2Node_CallFunction_16","K2Node_CallFunction_17","K2Node_CallFunction_18","K2Node_CallFunction_19",
 "K2Node_VariableGet_8","K2Node_VariableGet_9","K2Node_VariableGet_10","K2Node_VariableGet_11","K2Node_VariableGet_12",
 "K2Node_VariableSet_5","K2Node_VariableSet_6","K2Node_VariableSet_7","K2Node_VariableSet_8",
 "K2Node_Knot_13","K2Node_Knot_16"]
for n in data_del:
    print("del Data",n,bq("remove_node",graph_name="SetWallHandData",node_id=n))
print("del Front VariableGet_3:",bq("remove_node",graph_name="SetWallHandFront",node_id="K2Node_VariableGet_3"))
