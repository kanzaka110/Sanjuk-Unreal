import json, subprocess
MCP="http://localhost:9316/mcp"; BP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"; G="EventGraph"
GETTER="K2Node_CallFunction_7"; SETT="K2Node_VariableSet_5"; EVENT="K2Node_Event_0"; KML="KismetMathLibrary"; SPEEDZ="6.0"
OLD=["K2Node_CallFunction_15","K2Node_CallFunction_16","K2Node_CallFunction_17","K2Node_CallFunction_18","K2Node_CallFunction_19","K2Node_VariableGet_5","K2Node_VariableGet_6"]
log=[]
def w(s): log.append(str(s)); print(s)
def call(a,args):
    p={"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":"blueprint_query","arguments":{"action":a,**args}}}
    r=subprocess.run(["curl","-s","-X","POST",MCP,"-H","Content-Type: application/json","-d",json.dumps(p)],capture_output=True,text=True,timeout=40)
    try: return json.loads(json.loads(r.stdout)["result"]["content"][0]["text"])
    except Exception: return {"_raw":r.stdout[:150]}
def add(nt,x,y,**kw):
    r=call("add_node",{"asset_path":BP,"graph_name":G,"node_type":nt,"position":{"x":x,"y":y},**kw}); w(f"add {kw.get('function_name',nt)}->{r.get('id')}"); return r.get("id")
def C(sn,sp,tn,tp):
    r=call("connect_pins",{"asset_path":BP,"graph_name":G,"source_node":sn,"source_pin":sp,"target_node":tn,"target_pin":tp}); w(f"{'OK' if r.get('success') else 'FAIL'} {sn}.{sp}->{tn}.{tp}"+("" if r.get('success') else f" {r}"))
def D(n,pin,v): call("set_pin_default",{"asset_path":BP,"graph_name":G,"node_id":n,"pin_name":pin,"value":v})
for n in OLD: call("remove_node",{"asset_path":BP,"graph_name":G,"node_id":n}); w(f"rm {n}")
braw=add("CallFunction",780,1300,function_name="BreakVector",target_class=KML)
bcur=add("CallFunction",780,1450,function_name="BreakVector",target_class=KML)
curget=add("VariableGet",600,1450,variable_name="WallHandTarget")
fz=add("CallFunction",1000,1400,function_name="FInterpTo",target_class=KML)
mk=add("CallFunction",1200,1350,function_name="MakeVector",target_class=KML)
C(GETTER,"ReturnValue",braw,"InVec")
C(curget,"WallHandTarget",bcur,"InVec")
C(bcur,"Z",fz,"Current"); C(braw,"Z",fz,"Target"); C(EVENT,"DeltaTimeX",fz,"DeltaTime"); D(fz,"InterpSpeed",SPEEDZ)
C(braw,"X",mk,"X"); C(braw,"Y",mk,"Y"); C(fz,"ReturnValue",mk,"Z")
C(mk,"ReturnValue",SETT,"WallHandTarget")
w(str(call("compile_blueprint",{"asset_path":BP})))
open(r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\zonly.txt","w",encoding="utf-8").write("\n".join(log))
