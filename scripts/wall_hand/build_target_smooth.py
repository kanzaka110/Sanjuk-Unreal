"""타겟 스무딩: 레이어 읽기체인에서 getter -> VInterpTo -> Set WallHandTarget.
spine_03 bob/피드백으로 인한 타겟 Z 진동을 필터 → 팔 튐 제거.
getter=K2Node_CallFunction_7, Set=K2Node_VariableSet_5, Event=K2Node_Event_0(DeltaTimeX).
"""
import json, subprocess
MCP = "http://localhost:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"
G = "EventGraph"
GETTER = "K2Node_CallFunction_7"      # GetWallHandTargetWorld
SETT = "K2Node_VariableSet_5"         # Set WallHandTarget
EVENT = "K2Node_Event_0"              # BlueprintUpdateAnimation
SPEED = "10.0"                        # 스무딩 속도 노브 (낮을수록 부드럽고 lag↑)
log=[]
def w(s): log.append(str(s)); print(s)
def call(a,args):
    p={"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":"blueprint_query","arguments":{"action":a,**args}}}
    r=subprocess.run(["curl","-s","-X","POST",MCP,"-H","Content-Type: application/json","-d",json.dumps(p)],capture_output=True,text=True,timeout=40)
    try: return json.loads(json.loads(r.stdout)["result"]["content"][0]["text"])
    except Exception: return {"_raw":r.stdout[:200]}
def add(nt,x,y,**kw):
    r=call("add_node",{"asset_path":BP,"graph_name":G,"node_type":nt,"position":{"x":x,"y":y},**kw}); nid=r.get("id"); w(f"add {nt} {kw}->{nid}"+("" if nid else f" {r}")); return nid
def C(sn,sp,tn,tp):
    r=call("connect_pins",{"asset_path":BP,"graph_name":G,"source_node":sn,"source_pin":sp,"target_node":tn,"target_pin":tp}); w(f"  {'OK' if r.get('success') else 'FAIL'} {sn}.{sp}->{tn}.{tp}"+("" if r.get('success') else f" {r}"))

# 노드 추가
vget = add("VariableGet", 700, 1180, variable_name="WallHandTarget")   # 현재값
vinterp = add("CallFunction", 850, 1080, function_name="VInterpTo", target_class="KismetMathLibrary")
w("vinterp pins="+str([p['name'] for p in call('get_node_details',{'asset_path':BP,'graph_name':G,'node_id':vinterp}).get('pins',[])]))
# default speed
call("set_pin_default",{"asset_path":BP,"graph_name":G,"node_id":vinterp,"pin_name":"InterpSpeed","value":SPEED})

# 연결: Current<-현재 WallHandTarget, Target<-getter, DeltaTime<-event, Result->Set
C(vget,"WallHandTarget",vinterp,"Current")
C(GETTER,"ReturnValue",vinterp,"Target")
C(EVENT,"DeltaTimeX",vinterp,"DeltaTime")
C(vinterp,"ReturnValue",SETT,"WallHandTarget")   # 기존 getter->Set 입력 대체

w("=== compile ===")
w(str(call("compile_blueprint",{"asset_path":BP})))
with open(r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\target_smooth.txt","w",encoding="utf-8") as f: f.write("\n".join(log))
