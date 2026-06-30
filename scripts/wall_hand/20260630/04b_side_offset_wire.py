import urllib.request,json
BP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP";U="http://localhost:9316/mcp";G="UpdateWallHandIK"
ids=json.load(open(r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\f525ae6b-fccb-4356-b678-43eef9ec8640\scratchpad\offset_ids.json"))
def call(action,**p):
    p["asset_path"]=BP
    body=json.dumps({"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":"blueprint_query","arguments":{"action":action,"params":p}}}).encode()
    r=urllib.request.urlopen(urllib.request.Request(U,body,{"Content-Type":"application/json"}),timeout=40)
    d=json.loads(r.read());res=d.get("result",{});t=res.get("content",[{}])[0].get("text","")
    try:t=json.loads(t)
    except:pass
    return ("ERR" if res.get("isError") else "OK"),t
crs,nrm,sF,sS,sU,mF,mS,mU,a1,a2,aS=[ids[k] for k in("crs","nrm","sF","sS","sU","mF","mS","mU","a1","a2","aS")]
N0="K2Node_Knot_0";N62="K2Node_Knot_62";B102="K2Node_CallFunction_102"
conns=[
 (N0,"OutputPin",crs,"B"),
 (crs,"ReturnValue",nrm,"A"),
 (B102,"ReturnValue",sF,"bPickA"),(B102,"ReturnValue",sS,"bPickA"),(B102,"ReturnValue",sU,"bPickA"),
 (N0,"OutputPin",mF,"A"),(sF,"ReturnValue",mF,"B"),
 (nrm,"ReturnValue",mS,"A"),(sS,"ReturnValue",mS,"B"),
 (sU,"ReturnValue",mU,"B"),
 (mF,"ReturnValue",a1,"A"),(mS,"ReturnValue",a1,"B"),
 (a1,"ReturnValue",a2,"A"),(mU,"ReturnValue",a2,"B"),
 (N62,"OutputPin",aS,"A"),(a2,"ReturnValue",aS,"B"),
 (aS,"ReturnValue","K2Node_CallFunction_84","B"),
]
st,r=call("connect_pins_bulk",graph_name=G,connections=[{"source_node":s,"source_pin":sp,"target_node":t,"target_pin":tp} for s,sp,t,tp in conns])
print("wire:",st,json.dumps(r)[:140])
# defaults: world up on crs.A and mU.A ; 6 scalars 0
defs=[(crs,"A","0,0,1"),(mU,"A","0,0,1"),
      (sF,"A","0.0"),(sF,"B","0.0"),(sS,"A","0.0"),(sS,"B","0.0"),(sU,"A","0.0"),(sU,"B","0.0")]
st,r=call("set_pin_defaults_bulk",graph_name=G,defaults=[{"node_id":n,"pin_name":p,"value":v} for n,p,v in defs])
print("defaults:",st,json.dumps(r)[:140])
