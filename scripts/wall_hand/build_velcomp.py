import json, subprocess
MCP="http://localhost:9316/mcp"; BP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"; G="EventGraph"
GETTER="K2Node_CallFunction_7"; SETT="K2Node_VariableSet_5"; EVENT="K2Node_Event_0"
KML="KismetMathLibrary"; SPEED="8.0"
OLD=["K2Node_CallFunction_10","K2Node_CallFunction_11","K2Node_CallFunction_12","K2Node_CallFunction_13","K2Node_CallFunction_14"]
log=[]
def w(s): log.append(str(s)); print(s)
def call(a,args):
    p={"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":"blueprint_query","arguments":{"action":a,**args}}}
    r=subprocess.run(["curl","-s","-X","POST",MCP,"-H","Content-Type: application/json","-d",json.dumps(p)],capture_output=True,text=True,timeout=40)
    try: return json.loads(json.loads(r.stdout)["result"]["content"][0]["text"])
    except Exception: return {"_raw":r.stdout[:150]}
def add(nt,x,y,**kw):
    r=call("add_node",{"asset_path":BP,"graph_name":G,"node_type":nt,"position":{"x":x,"y":y},**kw}); nid=r.get("id"); w(f"add {kw.get('function_name',nt)}->{nid}"); return nid
def C(sn,sp,tn,tp):
    r=call("connect_pins",{"asset_path":BP,"graph_name":G,"source_node":sn,"source_pin":sp,"target_node":tn,"target_pin":tp}); w(f"{'OK' if r.get('success') else 'FAIL'} {sn}.{sp}->{tn}.{tp}"+("" if r.get('success') else f" {r}"))
def D(n,pin,v): call("set_pin_default",{"asset_path":BP,"graph_name":G,"node_id":n,"pin_name":pin,"value":v})
# 1) 기존 스무딩 노드 제거
for n in OLD:
    call("remove_node",{"asset_path":BP,"graph_name":G,"node_id":n}); w(f"rm {n}")
# 2) 새 노드: 액터위치, 오프셋, 스무딩, 복원
pawn=add("VariableGet",600,1400,variable_name="As SBCharacter")
loc=add("CallFunction",780,1400,function_name="GetActorLocation",target_class="Actor")
curget=add("VariableGet",600,1500,variable_name="WallHandTarget")
rawoff=add("CallFunction",950,1300,function_name="Subtract_VectorVector",target_class=KML)   # raw - actor
curoff=add("CallFunction",950,1500,function_name="Subtract_VectorVector",target_class=KML)   # cur - actor
vinterp=add("CallFunction",1150,1380,function_name="VInterpTo",target_class=KML)
addfin=add("CallFunction",1380,1380,function_name="Add_VectorVector",target_class=KML)        # actor + smoothOff
# 3) 연결
C(pawn,"As SBCharacter",loc,"self")
C(GETTER,"ReturnValue",rawoff,"A"); C(loc,"ReturnValue",rawoff,"B")
C(curget,"WallHandTarget",curoff,"A"); C(loc,"ReturnValue",curoff,"B")
C(curoff,"ReturnValue",vinterp,"Current"); C(rawoff,"ReturnValue",vinterp,"Target"); C(EVENT,"DeltaTimeX",vinterp,"DeltaTime")
D(vinterp,"InterpSpeed",SPEED)
C(loc,"ReturnValue",addfin,"A"); C(vinterp,"ReturnValue",addfin,"B")
C(addfin,"ReturnValue",SETT,"WallHandTarget")
w(str(call("compile_blueprint",{"asset_path":BP})))
open(r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\velcomp.txt","w",encoding="utf-8").write("\n".join(log))
