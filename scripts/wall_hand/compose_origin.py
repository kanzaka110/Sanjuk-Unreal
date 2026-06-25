import json, subprocess
MCP="http://localhost:9316/mcp"; BP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"; G="UpdateWallHandIK"
SOCK="K2Node_CallFunction_0"  # GetSocketLocation spine_05
KML="KismetMathLibrary"
# socket.ReturnValue 소비처 (T3D): traceR.Start=CF_5, addR.A=CF_3, Knot_5, Knot_3
CONSUMERS=[("K2Node_CallFunction_5","Start"),("K2Node_CallFunction_3","A"),("K2Node_Knot_5","InputPin"),("K2Node_Knot_3","InputPin")]
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
loc=add("CallFunction",-1376,-500,function_name="GetActorLocation",target_class="Actor")
ba=add("CallFunction",-1200,-500,function_name="BreakVector",target_class=KML)   # actor
bs=add("CallFunction",-1200,-350,function_name="BreakVector",target_class=KML)   # socket
mk=add("CallFunction",-1000,-450,function_name="MakeVector",target_class=KML)
C(loc,"ReturnValue",ba,"InVec")
C(SOCK,"ReturnValue",bs,"InVec")
C(ba,"X",mk,"X"); C(ba,"Y",mk,"Y"); C(bs,"Z",mk,"Z")
# 소비처를 composed 로 재배선 (socket->소비처를 대체)
for n,pin in CONSUMERS:
    C(mk,"ReturnValue",n,pin)
w(str(call("compile_blueprint",{"asset_path":BP})))
open(r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\compose.txt","w",encoding="utf-8").write("\n".join(log))
