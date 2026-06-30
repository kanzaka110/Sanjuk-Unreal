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
G="UpdateWallHandIK"
st,r=call("add_nodes_bulk",graph_name=G,nodes=[
 {"temp_id":"crs","node_type":"CallFunction","function_name":"Cross_VectorVector","target_class":KML,"position":[3400,1500]},
 {"temp_id":"nrm","node_type":"CallFunction","function_name":"Normal","target_class":KML,"position":[3560,1500]},
 {"temp_id":"sF","node_type":"CallFunction","function_name":"SelectFloat","target_class":KML,"position":[3400,1650]},
 {"temp_id":"sS","node_type":"CallFunction","function_name":"SelectFloat","target_class":KML,"position":[3400,1760]},
 {"temp_id":"sU","node_type":"CallFunction","function_name":"SelectFloat","target_class":KML,"position":[3400,1870]},
 {"temp_id":"mF","node_type":"CallFunction","function_name":"Multiply_VectorFloat","target_class":KML,"position":[3720,1600]},
 {"temp_id":"mS","node_type":"CallFunction","function_name":"Multiply_VectorFloat","target_class":KML,"position":[3720,1720]},
 {"temp_id":"mU","node_type":"CallFunction","function_name":"Multiply_VectorFloat","target_class":KML,"position":[3720,1840]},
 {"temp_id":"a1","node_type":"CallFunction","function_name":"Add_VectorVector","target_class":KML,"position":[3900,1650]},
 {"temp_id":"a2","node_type":"CallFunction","function_name":"Add_VectorVector","target_class":KML,"position":[4060,1700]},
 {"temp_id":"aS","node_type":"CallFunction","function_name":"Add_VectorVector","target_class":KML,"position":[4220,1750]},
])
print("add:",st)
ids={n["temp_id"]:n.get("node_id") for n in r.get("nodes_created",[])} if isinstance(r,dict) else {}
print("ids:",ids)
if st=="ERR": print("raw:",json.dumps(r)[:300])
import json as J
open(r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\f525ae6b-fccb-4356-b678-43eef9ec8640\scratchpad\offset_ids.json","w").write(J.dumps(ids))
