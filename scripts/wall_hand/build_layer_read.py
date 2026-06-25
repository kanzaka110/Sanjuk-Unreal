"""⑤-B: PC_01_AnimLayer_IK EventGraph에 ABP 읽기 체인 빌드.
then_2 -> GetAnimInstance -> Cast PC_01_ABP -> getter 2개 -> 레이어 var set.
"""
import json, subprocess
MCP = "http://localhost:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"
G = "EventGraph"
SEQ = "K2Node_ExecutionSequence_0"
ABPC = "PC_01_ABP_C"
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\layer_read.txt"
log = []
def w(s): log.append(str(s)); print(s)

def call(action, args):
    p = {"jsonrpc":"2.0","method":"tools/call","id":1,
         "params":{"name":"blueprint_query","arguments":{"action":action, **args}}}
    r = subprocess.run(["curl","-s","-X","POST",MCP,"-H","Content-Type: application/json","-d",json.dumps(p)],
                       capture_output=True, text=True, timeout=40)
    try:
        return json.loads(json.loads(r.stdout)["result"]["content"][0]["text"])
    except Exception:
        return {"_raw": r.stdout[:300]}

def add(nt, x, y, **kw):
    r = call("add_node", {"asset_path": BP, "graph_name": G, "node_type": nt, "position": {"x":x,"y":y}, **kw})
    nid = r.get("id")
    w(f"add {nt} {kw} -> {nid}" + ("" if nid else f" | {r}"))
    return nid

def pins(nid):
    d = call("get_node_details", {"asset_path": BP, "graph_name": G, "node_id": nid})
    return [(p["name"], p["direction"], p.get("type")) for p in d.get("pins", [])]

def C(sn,sp,tn,tp):
    r = call("connect_pins", {"asset_path": BP, "graph_name": G, "source_node": sn, "source_pin": sp, "target_node": tn, "target_pin": tp})
    w(f"  {'OK' if r.get('success') else 'FAIL'} {sn}.{sp}->{tn}.{tp}" + ("" if r.get('success') else f" | {r}"))

# 노드
goc = add("CallFunction", -100, 1100, function_name="GetOwningComponent", target_class="AnimInstance")
w(f"  goc pins={pins(goc)}")
gai = add("CallFunction", 150, 1100, function_name="GetAnimInstance", target_class="SkeletalMeshComponent")
w(f"  gai pins={pins(gai)}")
cast = add("DynamicCast", 450, 1100, cast_class=ABPC)
gt = add("CallFunction", 750, 1050, function_name="GetWallHandTargetWorld", target_class=ABPC)
st = add("VariableSet", 1000, 1050, variable_name="WallHandTarget")
ga = add("CallFunction", 750, 1250, function_name="GetWallHandAlphaValue", target_class=ABPC)
sa = add("VariableSet", 1000, 1250, variable_name="WallHandAlpha")
w(f"  cast pins={pins(cast)}")
w(f"  gt pins={pins(gt)}")
w(f"  st pins={pins(st)}")

# 데이터 연결
w("\n-- data --")
C(goc, "ReturnValue", gai, "self")
C(gai, "ReturnValue", cast, "Object")
C(cast, "AsPC 01 ABP", gt, "self")
C(cast, "AsPC 01 ABP", ga, "self")
C(gt, "ReturnValue", st, "WallHandTarget")
C(ga, "ReturnValue", sa, "WallHandAlpha")

# exec 체인
w("\n-- exec --")
C(SEQ, "then_2", gai, "execute")
C(gai, "then", cast, "execute")
C(cast, "then", gt, "execute")
C(gt, "then", st, "execute")
C(st, "then", ga, "execute")
C(ga, "then", sa, "execute")

w("\n=== compile ===")
w(str(call("compile_blueprint", {"asset_path": BP})))
with open(OUT,"w",encoding="utf-8") as f: f.write("\n".join(log))
