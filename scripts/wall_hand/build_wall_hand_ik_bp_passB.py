"""PC_01_BP 'UpdateWallHandIK' — Pass B: 연결 + 디폴트 + exec + Tick 삽입 + 컴파일.

Pass A에서 추가된 노드 ID 고정. BreakStruct는 GameplayStatics.BreakHitResult로 교체됨.
"""
import json
import subprocess

MCP = "http://localhost:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
FN = "UpdateWallHandIK"
OUT = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\wallhand_passB.txt"

# === 확정 노드 ID ===
entry = "K2Node_FunctionEntry_0"
mesh = "K2Node_VariableGet_0"
socket = "K2Node_CallFunction_0"      # GetSocketLocation  (pure)
right = "K2Node_CallFunction_1"       # GetActorRightVector (pure)
mulR = "K2Node_CallFunction_2"        # Multiply_VectorFloat (R*MaxDist)
addR = "K2Node_CallFunction_3"        # Add_VectorVector (RightEnd)
subL = "K2Node_CallFunction_4"        # Subtract_VectorVector (LeftEnd)
traceR = "K2Node_CallFunction_5"      # SphereTraceSingle R
traceL = "K2Node_CallFunction_6"      # SphereTraceSingle L
effR = "K2Node_CallFunction_7"        # SelectFloat
effL = "K2Node_CallFunction_8"        # SelectFloat
bRight = "K2Node_CallFunction_9"      # LessEqual_DoubleDouble
selImpact = "K2Node_CallFunction_10"  # SelectVector
selNormal = "K2Node_CallFunction_11"  # SelectVector
mulOff = "K2Node_CallFunction_12"     # Multiply_VectorFloat (Normal*HandThickness)
addTgt = "K2Node_CallFunction_13"     # Add_VectorVector (Target)
orHit = "K2Node_CallFunction_14"      # BooleanOR
selAlpha = "K2Node_CallFunction_15"   # SelectFloat
animInst = "K2Node_CallFunction_16"   # GetAnimInstance (pure)
breakR = "K2Node_CallFunction_18"     # BreakHitResult
breakL = "K2Node_CallFunction_19"     # BreakHitResult
cast = "K2Node_DynamicCast_0"         # Cast To PC_01_ABP
setter = "K2Node_CallFunction_20"     # SetWallHandData
CAST_OUT = "AsPC 01 ABP"

log = []


def p(s):
    log.append(str(s)); print(s)


def call(action, args):
    payload = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
               "params": {"name": "blueprint_query",
                          "arguments": {"action": action, **args}}}
    r = subprocess.run(["curl", "-s", "-X", "POST", MCP, "-H",
                        "Content-Type: application/json", "-d", json.dumps(payload)],
                       capture_output=True, text=True, timeout=40)
    try:
        d = json.loads(r.stdout)
        return json.loads(d["result"]["content"][0]["text"])
    except Exception:
        return {"_raw": r.stdout[:300]}


def C(sn, sp, tn, tp):
    res = call("connect_pins", {"asset_path": BP, "graph_name": FN,
                                "source_node": sn, "source_pin": sp,
                                "target_node": tn, "target_pin": tp})
    ok = res.get("success", False)
    p(f"  {'OK ' if ok else 'FAIL'} {sn}.{sp} -> {tn}.{tp}" + ("" if ok else f" | {res}"))
    return ok


def D(n, pin, val):
    res = call("set_pin_default", {"asset_path": BP, "graph_name": FN,
                                   "node_id": n, "pin_name": pin, "value": val})
    ok = res.get("success", False)
    p(f"  {'OK ' if ok else 'FAIL'} default {n}.{pin}={val}" + ("" if ok else f" | {res}"))


p("=== DATA 연결 ===")
# Origin / direction
C(mesh, "Mesh", socket, "self")
C(socket, "ReturnValue", addR, "A")
C(socket, "ReturnValue", subL, "A")
C(socket, "ReturnValue", traceR, "Start")
C(socket, "ReturnValue", traceL, "Start")
C(right, "ReturnValue", mulR, "A")
C(mulR, "ReturnValue", addR, "B")
C(mulR, "ReturnValue", subL, "B")
C(addR, "ReturnValue", traceR, "End")
C(subL, "ReturnValue", traceL, "End")
# trace -> break
C(traceR, "OutHit", breakR, "Hit")
C(traceL, "OutHit", breakL, "Hit")
# nearest 선택
C(breakR, "Distance", effR, "A")
C(breakL, "Distance", effL, "A")
C(traceR, "ReturnValue", effR, "bPickA")
C(traceL, "ReturnValue", effL, "bPickA")
C(effR, "ReturnValue", bRight, "A")
C(effL, "ReturnValue", bRight, "B")
# side gate
C(bRight, "ReturnValue", selImpact, "bPickA")
C(bRight, "ReturnValue", selNormal, "bPickA")
C(bRight, "ReturnValue", setter, "InRight")
C(breakR, "ImpactPoint", selImpact, "A")
C(breakL, "ImpactPoint", selImpact, "B")
C(breakR, "ImpactNormal", selNormal, "A")
C(breakL, "ImpactNormal", selNormal, "B")
# target = impact + normal*thickness
C(selNormal, "ReturnValue", mulOff, "A")
C(selImpact, "ReturnValue", addTgt, "A")
C(mulOff, "ReturnValue", addTgt, "B")
C(addTgt, "ReturnValue", setter, "InTargetWorld")
C(selNormal, "ReturnValue", setter, "InNormal")
# alpha = hitAny ? 1 : 0
C(traceR, "ReturnValue", orHit, "A")
C(traceL, "ReturnValue", orHit, "B")
C(orHit, "ReturnValue", selAlpha, "bPickA")
C(selAlpha, "ReturnValue", setter, "InAlphaTarget")
# anim instance -> cast -> setter.self
C(mesh, "Mesh", animInst, "self")
C(animInst, "ReturnValue", cast, "Object")
C(cast, CAST_OUT, setter, "self")

p("\n=== EXEC 체인 ===")
C(entry, "then", traceR, "execute")
C(traceR, "then", traceL, "execute")
C(traceL, "then", cast, "execute")
C(cast, "then", setter, "execute")

p("\n=== 핀 디폴트 ===")
D(socket, "InSocketName", "spine_03")
D(mulR, "B", "60.0")
D(traceR, "Radius", "15.0")
D(traceL, "Radius", "15.0")
D(traceR, "bIgnoreSelf", "true")
D(traceL, "bIgnoreSelf", "true")
D(effR, "B", "99999.0")
D(effL, "B", "99999.0")
D(mulOff, "B", "4.0")
D(selAlpha, "A", "1.0")
D(selAlpha, "B", "0.0")

p("\n=== Tick 삽입 (EventGraph) ===")
# UpdateWallHandIK 호출 노드 (self)
res = call("add_node", {"asset_path": BP, "graph_name": "EventGraph",
                        "node_type": "CallFunction", "position": [88, 1100],
                        "function_name": FN, "target_class": "PC_01_BP_C"})
callnode = res.get("id")
p(f"  call node = {callnode} | {res if not callnode else ''}")
if callnode:
    # Event.then <-> Sequence.execute 끊고 사이에 삽입
    dis = call("disconnect_pins", {"asset_path": BP, "graph_name": "EventGraph",
                                   "source_node": "K2Node_Event_2", "source_pin": "then",
                                   "target_node": "K2Node_ExecutionSequence_1", "target_pin": "execute"})
    p(f"  disconnect Event.then-Seq.execute: {dis.get('success', dis)}")

    def CE(sn, sp, tn, tp):
        res = call("connect_pins", {"asset_path": BP, "graph_name": "EventGraph",
                                    "source_node": sn, "source_pin": sp,
                                    "target_node": tn, "target_pin": tp})
        p(f"  {'OK ' if res.get('success') else 'FAIL'} {sn}.{sp}->{tn}.{tp}" + ("" if res.get('success') else f" | {res}"))
    CE("K2Node_Event_2", "then", callnode, "execute")
    CE(callnode, "then", "K2Node_ExecutionSequence_1", "execute")

p("\n=== 컴파일 ===")
p(call("compile_blueprint", {"asset_path": BP}))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(log))
print(f"\nWROTE {OUT}")
