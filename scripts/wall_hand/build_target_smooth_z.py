"""타겟 Z만 스무딩 (X/Y는 raw=즉시추적). 전체벡터 VInterpTo(CF_9) 제거 후 Break/FInterpTo(Z)/Make 로 교체.
Y(보행) lag 제거 → 손 뒤로 빠짐 해결, Z bob만 필터.
"""
import json, subprocess
MCP="http://localhost:9316/mcp"; BP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"; G="EventGraph"
GETTER="K2Node_CallFunction_7"; SETT="K2Node_VariableSet_5"; EVENT="K2Node_Event_0"
OLD_VINTERP="K2Node_CallFunction_9"; CUR_GET="K2Node_VariableGet_4"
KML="KismetMathLibrary"; SPEEDZ="8.0"
log=[]
def w(s): log.append(str(s)); print(s)
def call(a,args):
    p={"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":"blueprint_query","arguments":{"action":a,**args}}}
    r=subprocess.run(["curl","-s","-X","POST",MCP,"-H","Content-Type: application/json","-d",json.dumps(p)],capture_output=True,text=True,timeout=40)
    try: return json.loads(json.loads(r.stdout)["result"]["content"][0]["text"])
    except Exception: return {"_raw":r.stdout[:200]}
def add(nt,x,y,**kw):
    r=call("add_node",{"asset_path":BP,"graph_name":G,"node_type":nt,"position":{"x":x,"y":y},**kw}); nid=r.get("id"); w(f"add {nt} {kw}->{nid}"+("" if nid else f" {r}")); return nid
def pins(nid): return [p['name'] for p in call('get_node_details',{'asset_path':BP,'graph_name':G,'node_id':nid}).get('pins',[])]
def C(sn,sp,tn,tp):
    r=call("connect_pins",{"asset_path":BP,"graph_name":G,"source_node":sn,"source_pin":sp,"target_node":tn,"target_pin":tp}); w(f"  {'OK' if r.get('success') else 'FAIL'} {sn}.{sp}->{tn}.{tp}"+("" if r.get('success') else f" {r}"))

# 1) 기존 전체벡터 VInterpTo 제거
w(str(call("remove_node",{"asset_path":BP,"graph_name":G,"node_id":OLD_VINTERP})))

# 2) Break(raw getter), Break(current), FInterpTo(Z), Make
braw=add("CallFunction",780,1060,function_name="BreakVector",target_class=KML)
bcur=add("CallFunction",780,1200,function_name="BreakVector",target_class=KML)
fz=add("CallFunction",1000,1140,function_name="FInterpTo",target_class=KML)
mk=add("CallFunction",1200,1060,function_name="MakeVector",target_class=KML)
w("braw="+str(pins(braw))+" fz="+str(pins(fz))+" mk="+str(pins(mk)))
call("set_pin_default",{"asset_path":BP,"graph_name":G,"node_id":fz,"pin_name":"InterpSpeed","value":SPEEDZ})

# 연결
C(GETTER,"ReturnValue",braw,"InVec")
C(CUR_GET,"WallHandTarget",bcur,"InVec")
C(bcur,"Z",fz,"Current")
C(braw,"Z",fz,"Target")
C(EVENT,"DeltaTimeX",fz,"DeltaTime")
C(braw,"X",mk,"X")
C(braw,"Y",mk,"Y")
C(fz,"ReturnValue",mk,"Z")
C(mk,"ReturnValue",SETT,"WallHandTarget")

w("=== compile ===")
w(str(call("compile_blueprint",{"asset_path":BP})))
with open(r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\target_smooth_z.txt","w",encoding="utf-8") as f: f.write("\n".join(log))
