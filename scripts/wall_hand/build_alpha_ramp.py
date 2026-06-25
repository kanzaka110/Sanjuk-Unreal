"""AlphaTarget을 이진(히트→1.0)에서 '거리 램프'로 교체.
nearestDist = SelectFloat(effR, effL, bRight) ; alpha = MapRangeClamped(dist, FAR, NEAR, 0, 1).
가까울수록 alpha↑ → 손IK·몸회전 등 비례. (selAlpha CF_15 → orphan)
PC_01_BP / UpdateWallHandIK. effR=CF_7 effL=CF_8 bRight=CF_9 setter.InAlphaTarget via Knot_25.
"""
import json, subprocess
MCP="http://localhost:9316/mcp"; BP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"; G="UpdateWallHandIK"
FAR="55.0"; NEAR="15.0"   # 거리 램프 노브(cm): FAR→alpha0, NEAR→alpha1
log=[]
def w(s): log.append(str(s)); print(s)
def call(a,args):
    p={"jsonrpc":"2.0","method":"tools/call","id":1,"params":{"name":"blueprint_query","arguments":{"action":a,**args}}}
    r=subprocess.run(["curl","-s","-X","POST",MCP,"-H","Content-Type: application/json","-d",json.dumps(p)],capture_output=True,text=True,timeout=40)
    try: return json.loads(json.loads(r.stdout)["result"]["content"][0]["text"])
    except Exception: return {"_raw":r.stdout[:200]}
def add(nt,x,y,**kw):
    r=call("add_node",{"asset_path":BP,"graph_name":G,"node_type":nt,"position":{"x":x,"y":y},**kw}); nid=r.get("id"); w(f"add {kw}->{nid}"); return nid
def pins(nid): return [p['name'] for p in call('get_node_details',{'asset_path':BP,'graph_name':G,'node_id':nid}).get('pins',[])]
def C(sn,sp,tn,tp):
    r=call("connect_pins",{"asset_path":BP,"graph_name":G,"source_node":sn,"source_pin":sp,"target_node":tn,"target_pin":tp}); w(f"  {'OK' if r.get('success') else 'FAIL'} {sn}.{sp}->{tn}.{tp}"+("" if r.get('success') else f" {r}"))
def D(n,pin,v):
    r=call("set_pin_default",{"asset_path":BP,"graph_name":G,"node_id":n,"pin_name":pin,"value":v}); w(f"  {'OK' if r.get('success') else 'FAIL'} {n}.{pin}={v}")

nd=add("CallFunction",1500,-400,function_name="SelectFloat",target_class="KismetMathLibrary")     # nearestDist
mp=add("CallFunction",1750,-400,function_name="MapRangeClamped",target_class="KismetMathLibrary")
w("map pins="+str(pins(mp)))
# nearestDist = SelectFloat(effR, effL, bRight)
C("K2Node_CallFunction_7","ReturnValue",nd,"A")
C("K2Node_CallFunction_8","ReturnValue",nd,"B")
C("K2Node_CallFunction_9","ReturnValue",nd,"bPickA")
# map(Value=dist)
C(nd,"ReturnValue",mp,"Value")
D(mp,"InRangeA",FAR); D(mp,"InRangeB",NEAR); D(mp,"OutRangeA","0.0"); D(mp,"OutRangeB","1.0")
# map -> setter.InAlphaTarget (Knot_25 입력 대체)
C(mp,"ReturnValue","K2Node_Knot_25","InputPin")
w("=== compile ===")
w(str(call("compile_blueprint",{"asset_path":BP})))
open(r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\alpha_ramp.txt","w",encoding="utf-8").write("\n".join(log))
