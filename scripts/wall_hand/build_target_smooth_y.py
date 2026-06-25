import json, subprocess
MCP="http://localhost:9316/mcp"; BP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"; G="EventGraph"
BRAW="K2Node_CallFunction_10"; BCUR="K2Node_CallFunction_11"; FZ="K2Node_CallFunction_12"; MK="K2Node_CallFunction_13"; EVENT="K2Node_Event_0"
SPEEDY="10.0"; SPEEDZ="6.0"
log=[]
def w(s): log.append(str(s)); print(s)
def call(a,args):
    p={"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":"blueprint_query","arguments":{"action":a,**args}}}
    r=subprocess.run(["curl","-s","-X","POST",MCP,"-H","Content-Type: application/json","-d",json.dumps(p)],capture_output=True,text=True,timeout=40)
    try: return json.loads(json.loads(r.stdout)["result"]["content"][0]["text"])
    except Exception: return {"_raw":r.stdout[:150]}
def C(sn,sp,tn,tp):
    r=call("connect_pins",{"asset_path":BP,"graph_name":G,"source_node":sn,"source_pin":sp,"target_node":tn,"target_pin":tp}); w(f"{'OK' if r.get('success') else 'FAIL'} {sn}.{sp}->{tn}.{tp}"+("" if r.get('success') else f" {r}"))
def D(n,pin,v):
    r=call("set_pin_default",{"asset_path":BP,"graph_name":G,"node_id":n,"pin_name":pin,"value":v}); w(f"{'OK' if r.get('success') else 'FAIL'} {n}.{pin}={v}")
# Y 스무딩 노드
r=call("add_node",{"asset_path":BP,"graph_name":G,"node_type":"CallFunction","position":{"x":850,"y":1300},"function_name":"FInterpTo","target_class":"KismetMathLibrary"})
fy=r.get("id"); w(f"fy={fy}")
C(BCUR,"Y",fy,"Current")
C(BRAW,"Y",fy,"Target")
C(EVENT,"DeltaTimeX",fy,"DeltaTime")
D(fy,"InterpSpeed",SPEEDY)
C(fy,"ReturnValue",MK,"Y")   # raw Y 대체
# Z 스무딩 강화
D(FZ,"InterpSpeed",SPEEDZ)
w(str(call("compile_blueprint",{"asset_path":BP})))
open(r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\smooth_y.txt","w",encoding="utf-8").write("\n".join(log))
