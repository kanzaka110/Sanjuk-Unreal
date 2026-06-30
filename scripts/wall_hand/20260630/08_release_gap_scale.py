import urllib.request,json
A="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP";U="http://localhost:9316/mcp";KML="/Script/Engine.KismetMathLibrary";G="SetSmoothedWallHandAlpha"
def call(action,**p):
    p["asset_path"]=A
    body=json.dumps({"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":"blueprint_query","arguments":{"action":action,"params":p}}}).encode()
    r=urllib.request.urlopen(urllib.request.Request(U,body,{"Content-Type":"application/json"}),timeout=40)
    d=json.loads(r.read());res=d.get("result",{});t=res.get("content",[{}])[0].get("text","")
    try:t=json.loads(t)
    except:pass
    return ("ERR" if res.get("isError") else "OK"),t
st,r=call("add_nodes_bulk",graph_name=G,nodes=[
 {"temp_id":"sub","node_type":"CallFunction","function_name":"Subtract_DoubleDouble","target_class":KML,"position":[-700,400]},
 {"temp_id":"mul","node_type":"CallFunction","function_name":"Multiply_DoubleDouble","target_class":KML,"position":[-540,400]},
 {"temp_id":"add","node_type":"CallFunction","function_name":"Add_DoubleDouble","target_class":KML,"position":[-380,400]},
])
print("add:",st)
ids={n["temp_id"]:n.get("node_id") for n in r.get("nodes_created",[])} if isinstance(r,dict) else {}
print("ids:",ids, json.dumps(r)[:150] if st=="ERR" else "")
sub,mul,add=ids.get("sub"),ids.get("mul"),ids.get("add")
# sub = WallHandAlpha(current, VariableGet_0) - WallHandAlphaTarget(VariableGet_1)
conns=[("K2Node_VariableGet_0","WallHandAlpha",sub,"A"),
       ("K2Node_VariableGet_1","WallHandAlphaTarget",sub,"B"),
       (sub,"ReturnValue",mul,"A"),
       (mul,"ReturnValue",add,"A"),
       (add,"ReturnValue","K2Node_CallFunction_2","A")]
st,r=call("connect_pins_bulk",graph_name=G,connections=[{"source_node":s,"source_pin":sp,"target_node":t,"target_pin":tp} for s,sp,t,tp in conns])
print("wire:",st,json.dumps(r)[:120])
st,r=call("set_pin_defaults_bulk",graph_name=G,defaults=[{"node_id":mul,"pin_name":"B","value":"12.0"},{"node_id":add,"pin_name":"B","value":"3.0"}])
print("defaults(K=12,base=3):",st,json.dumps(r)[:100])
