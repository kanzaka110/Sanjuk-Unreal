import json, subprocess
MCP="http://localhost:9316/mcp"; BP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"; G="UpdateWallHandIK"; KML="KismetMathLibrary"
ENTRY="K2Node_FunctionEntry_0"; TRACER="K2Node_CallFunction_5"; RAWVEL="K2Node_CallFunction_26"; LEADMUL="K2Node_CallFunction_27"
VSPEED="12.0"; DT="0.016667"
log=[]
def w(s): log.append(str(s)); print(s)
def call(a,args):
    p={"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":"blueprint_query","arguments":{"action":a,**args}}}
    r=subprocess.run(["curl","-s","-X","POST",MCP,"-H","Content-Type: application/json","-d",json.dumps(p)],capture_output=True,text=True,timeout=40)
    try: return json.loads(json.loads(r.stdout)["result"]["content"][0]["text"])
    except Exception: return {"_raw":r.stdout[:150]}
def add(nt,x,y,**kw):
    r=call("add_node",{"asset_path":BP,"graph_name":G,"node_type":nt,"position":{"x":x,"y":y},**kw}); w(f"add {kw.get('function_name',kw.get('variable_name',nt))}->{r.get('id')}"); return r.get("id")
def C(sn,sp,tn,tp):
    r=call("connect_pins",{"asset_path":BP,"graph_name":G,"source_node":sn,"source_pin":sp,"target_node":tn,"target_pin":tp}); w(f"{'OK' if r.get('success') else 'FAIL'} {sn}.{sp}->{tn}.{tp}"+("" if r.get('success') else f" {r}"))
def D(n,pin,v): call("set_pin_default",{"asset_path":BP,"graph_name":G,"node_id":n,"pin_name":pin,"value":v})
getv=add("VariableGet",-1900,-750,variable_name="WallHandSmoothVel")
vinterp=add("CallFunction",-1750,-700,function_name="VInterpTo",target_class=KML)
setv=add("VariableSet",-1750,-820,variable_name="WallHandSmoothVel")
C(getv,"WallHandSmoothVel",vinterp,"Current")
C(RAWVEL,"ReturnValue",vinterp,"Target")
D(vinterp,"DeltaTime",DT); D(vinterp,"InterpSpeed",VSPEED)
C(vinterp,"ReturnValue",setv,"WallHandSmoothVel")
# lead mul 입력을 raw vel -> smoothed vel 로
C(vinterp,"ReturnValue",LEADMUL,"A")
# exec: Entry -> SetVel -> traceR
C(ENTRY,"then",setv,"execute")
C(setv,"then",TRACER,"execute")
w(str(call("compile_blueprint",{"asset_path":BP})))
open(r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\smoothvel.txt","w",encoding="utf-8").write("\n".join(log))
