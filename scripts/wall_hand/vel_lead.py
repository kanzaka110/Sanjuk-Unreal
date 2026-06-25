import json, subprocess
MCP="http://localhost:9316/mcp"; BP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"; G="UpdateWallHandIK"; KML="KismetMathLibrary"
ALOC="K2Node_CallFunction_22"  # GetActorLocation
BACT="K2Node_CallFunction_23"  # BreakVector(actor)
LEAD="0.040000"   # 리드 시간(초) 노브 — 뒤처지면 키우고, 앞서가면 줄임
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
vel=add("CallFunction",-1600,-650,function_name="GetVelocity",target_class="Actor")
mul=add("CallFunction",-1400,-650,function_name="Multiply_VectorFloat",target_class=KML)
addl=add("CallFunction",-1300,-560,function_name="Add_VectorVector",target_class=KML)
C(vel,"ReturnValue",mul,"A"); D(mul,"B",LEAD)
C(ALOC,"ReturnValue",addl,"A"); C(mul,"ReturnValue",addl,"B")
# BreakVector(actor) 입력을 actorLoc -> actorLead 로 대체
C(addl,"ReturnValue",BACT,"InVec")
w(str(call("compile_blueprint",{"asset_path":BP})))
open(r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\vellead.txt","w",encoding="utf-8").write("\n".join(log))
