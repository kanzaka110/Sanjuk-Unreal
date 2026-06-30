import urllib.request,json
ABP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
BP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
U="http://localhost:9316/mcp";KML="/Script/Engine.KismetMathLibrary"
def call(asset,action,**p):
    p["asset_path"]=asset
    body=json.dumps({"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":"blueprint_query","arguments":{"action":action,"params":p}}}).encode()
    r=urllib.request.urlopen(urllib.request.Request(U,body,{"Content-Type":"application/json"}),timeout=30)
    d=json.loads(r.read());res=d.get("result",{});t=res.get("content",[{}])[0].get("text","")
    try:t=json.loads(t)
    except:pass
    return ("ERR" if res.get("isError") else "OK"),t

# ABP: InBlendSpeed param -> InterpSpeed (both)
print("Data CF_2.InterpSpeed<-InBlendSpeed:",call(ABP,"connect_pins",graph_name="SetWallHandData",source_node="K2Node_FunctionEntry_0",source_pin="InBlendSpeed",target_node="K2Node_CallFunction_2",target_pin="InterpSpeed")[0])
print("Front CF_4.InterpSpeed<-InBlendSpeed:",call(ABP,"connect_pins",graph_name="SetWallHandFront",source_node="K2Node_FunctionEntry_0",source_pin="InBlendSpeed",target_node="K2Node_CallFunction_4",target_pin="InterpSpeed")[0])

# BP: add VSizeXY + MapRangeClamped
st,r=call(BP,"add_nodes_bulk",graph_name="UpdateWallHandIK",nodes=[
 {"temp_id":"vsz","node_type":"CallFunction","function_name":"VSizeXY","target_class":KML,"position":[200,1400]},
 {"temp_id":"mrc","node_type":"CallFunction","function_name":"MapRangeClamped","target_class":KML,"position":[420,1400]},
])
print("BP add nodes:",st)
ids={n["temp_id"]:n["node_id"] for n in r.get("nodes_created",[])} if isinstance(r,dict) else {}
vsz,mrc=ids.get("vsz"),ids.get("mrc")
print("  vsz=%s mrc=%s"%(vsz,mrc))
# defaults on MapRangeClamped: In 0->400, Out 15->4
for pin,val in (("InRangeA","0.0"),("InRangeB","400.0"),("OutRangeA","15.0"),("OutRangeB","4.0")):
    call(BP,"set_pin_default",graph_name="UpdateWallHandIK",node_id=mrc,pin_name=pin,value=val)
print("  mrc defaults set 0/400/15/4")
# wire: CF_26.Velocity -> vsz.A ; vsz.RV -> mrc.Value ; mrc.RV -> CF_20.InBlendSpeed & CF_86.InBlendSpeed
conns=[("K2Node_CallFunction_26","ReturnValue",vsz,"A"),
       (vsz,"ReturnValue",mrc,"Value"),
       (mrc,"ReturnValue","K2Node_CallFunction_20","InBlendSpeed"),
       (mrc,"ReturnValue","K2Node_CallFunction_86","InBlendSpeed")]
st,r=call(BP,"connect_pins_bulk",graph_name="UpdateWallHandIK",connections=[{"source_node":s,"source_pin":sp,"target_node":t,"target_pin":tp} for s,sp,t,tp in conns])
print("BP wire:",st,json.dumps(r)[:160])
