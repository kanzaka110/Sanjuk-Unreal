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
 {"temp_id":"gsl","node_type":"CallFunction","function_name":"GetSocketLocation","position":[3300,2100]},
 {"temp_id":"brk","node_type":"break_struct","position":[3520,2100]},
])
print("add:",st)
ids={n["temp_id"]:n.get("node_id") for n in r.get("nodes_created",[])} if isinstance(r,dict) else {}
print("ids:",ids, "raw:" + json.dumps(r)[:200] if st=="ERR" else "")
gsl,brk=ids.get("gsl"),ids.get("brk")
if gsl:
    # connect Mesh -> gsl.self, set socket name
    print("Mesh->gsl.self:",call("connect_pins",graph_name=G,source_node="K2Node_VariableGet_0",source_pin="Mesh",target_node=gsl,target_pin="self")[0])
    print("gsl.InSocketName=spine_03:",call("set_pin_default",graph_name=G,node_id=gsl,pin_name="InSocketName",value="spine_03")[0])
    st2,r2=call("get_node_details",graph_name=G,node_id=gsl)
    if isinstance(r2,dict): print("gsl pins:",[(p['name'],p['direction']) for p in r2['pins']])
if brk:
    st3,r3=call("get_node_details",graph_name=G,node_id=brk)
    if isinstance(r3,dict): print("brk pins:",[(p['name'],p['direction'],p.get('type')) for p in r3['pins']])
import json as J
open(r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\f525ae6b-fccb-4356-b678-43eef9ec8640\scratchpad\spine_ids.json","w").write(J.dumps(ids))
