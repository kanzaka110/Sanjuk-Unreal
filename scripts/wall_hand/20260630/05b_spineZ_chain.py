import urllib.request,json
BP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP";U="http://localhost:9316/mcp";KML="/Script/Engine.KismetMathLibrary"
def call(action,**p):
    p["asset_path"]=BP
    body=json.dumps({"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":"blueprint_query","arguments":{"action":action,"params":p}}}).encode()
    r=urllib.request.urlopen(urllib.request.Request(U,body,{"Content-Type":"application/json"}),timeout=40)
    d=json.loads(r.read());res=d.get("result",{});t=res.get("content",[{}])[0].get("text","")
    try:t=json.loads(t)
    except:pass
    return ("ERR" if res.get("isError") else "OK"),t
G="UpdateWallHandIK"; GSL="K2Node_CallFunction_39"
st,r=call("add_nodes_bulk",graph_name=G,nodes=[
 {"temp_id":"dot","node_type":"CallFunction","function_name":"Dot_VectorVector","target_class":KML,"position":[3520,2100]},
 {"temp_id":"sR","node_type":"CallFunction","function_name":"Subtract_DoubleDouble","target_class":KML,"position":[3700,2080]},
 {"temp_id":"sC","node_type":"CallFunction","function_name":"Subtract_DoubleDouble","target_class":KML,"position":[3860,2080]},
 {"temp_id":"ml","node_type":"CallFunction","function_name":"Multiply_DoubleDouble","target_class":KML,"position":[4020,2080]},
 {"temp_id":"mkv","node_type":"CallFunction","function_name":"MakeVector","target_class":KML,"position":[4180,2100]},
 {"temp_id":"adz","node_type":"CallFunction","function_name":"Add_VectorVector","target_class":KML,"position":[4360,1820]},
])
print("add:",st)
ids={n["temp_id"]:n.get("node_id") for n in r.get("nodes_created",[])} if isinstance(r,dict) else {}
print("ids:",ids)
dot,sR,sC,ml,mkv,adz=[ids[k] for k in("dot","sR","sC","ml","mkv","adz")]
conns=[
 (GSL,"ReturnValue",dot,"A"),
 (dot,"ReturnValue",sR,"A"),("K2Node_CallFunction_34","Z",sR,"B"),
 (sR,"ReturnValue",sC,"A"),
 (sC,"ReturnValue",ml,"A"),
 (ml,"ReturnValue",mkv,"Z"),
 ("K2Node_CallFunction_90","ReturnValue",adz,"A"),(mkv,"ReturnValue",adz,"B"),
 (adz,"ReturnValue","K2Node_CallFunction_84","B"),
]
st,r=call("connect_pins_bulk",graph_name=G,connections=[{"source_node":s,"source_pin":sp,"target_node":t,"target_pin":tp} for s,sp,t,tp in conns])
print("wire:",st,json.dumps(r)[:120])
defs=[(dot,"B","0,0,1"),(sC,"B","0.0"),(ml,"B","0.3"),(mkv,"X","0.0"),(mkv,"Y","0.0")]
st,r=call("set_pin_defaults_bulk",graph_name=G,defaults=[{"node_id":n,"pin_name":p,"value":v} for n,p,v in defs])
print("defaults:",st,json.dumps(r)[:120])
import json as J
open(r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\f525ae6b-fccb-4356-b678-43eef9ec8640\scratchpad\spine_chain_ids.json","w").write(J.dumps(ids))
