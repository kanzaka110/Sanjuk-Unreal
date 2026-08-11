# -*- coding: utf-8 -*-
"""렛지 스무딩 2건 일괄 적용 (2026-08-11)

[A] 골반 스프링 게이트 이징 — PC_01_ABP / LedgeIK
  현재: GetCurveValue("ledge_pelvis_spring") 생값 -> Set LedgePelvisSpring
  문제: 커브가 모디파이어 템플릿(Start/Full/HoldEnd/End) 을 직선으로 이은 사다리꼴이라
        켜짐/최대/꺼짐 네 모서리에서 기울기가 꺾인다 -> 스프링이 툭 걸리고 툭 풀림
  수정: Ease(A=0,B=1,Alpha=커브,SinusoidalInOut,BlendExp=2) 1노드 삽입
        지연 0 / 타이밍·진폭·CR 파라미터(강성 3.0, 감쇠 0.25, 비율 Y0.9 Z0.5, 클램프 45) 불변
        커브 재베이크 없음. 되돌리려면 EasingFunc=Linear 로만 바꿔도 원복.

[B] 시선 AO 를 "매달린 Idle" 로 한정 — PC_01_AnimLayer_Ledge / UpdateLedgeLook
  현재 게이트: bActive AND 시선편차>0.35 AND !bUnitMoveInProgress AND !bTransitingToNextLedge
  문제: 시선 BS(BS_LedgeSeeking_*)는 additive 가 아니라 전신 애님(3s 루프)이고
        양방향 블렌드로 LinkedInputPose 를 통째로 대체한다. 위 게이트가 진입/이탈/코너
        이벤트 애님 구간을 못 막아서 그 구간 원본 애님이 갈려나감 -> "애니메이션이 끊김"
  수정: PC_01_ABP.LedgeState 에 출력 LedgeLookIdle(bool) 추가
        = LedgeStopped AND NOT bLedgeEventAnim
        -> 레이어 변수로 캡처 -> UpdateLedgeLook AND 체인에 합류

주의: 근본 처방(양방향블렌드 -> LayeredBoneBlend)은 이 스크립트 범위 밖. PIE 확인 후 별건.
"""
import json
import sys
import urllib.request

MCP = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
LAY = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge"
KML = "KismetMathLibrary"

# [A] LedgeIK
G_IK = "LedgeIK"
CURVE_GET = "K2Node_CallFunction_44"   # GetCurveValue("ledge_pelvis_spring")
SPRING_SET = "K2Node_VariableSet_15"   # Set LedgePelvisSpring

# [B]
G_STATE = "LedgeState"
STATE_RESULT = "K2Node_FunctionResult_0"
G_LOOK = "UpdateLedgeLook"
LOOK_AND = "K2Node_CallFunction_17"    # 마지막 AND
LOOK_SEL = "K2Node_CallFunction_18"    # SelectFloat(bPickA)
LAY_EG = "EventGraph"
LEDGESTATE_CALL = "K2Node_CallFunction_34"

LOG = []


def w(s):
    LOG.append(str(s))
    print(s)


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(MCP, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError("%s: %s" % (action, txt[:600]))
    try:
        return json.loads(txt)
    except Exception:
        return {"raw": txt}


def bp(action, params, timeout=300):
    return call("blueprint_query", action, params, timeout)


def nd(asset, graph, node_id):
    return bp("get_node_details", {"asset_path": asset, "graph_name": graph, "node_id": node_id})


def pin(d, name):
    for p in d["pins"]:
        if p["name"] == name:
            return p
    raise KeyError("pin %s not in %s (%s)" % (name, d["id"], [p["name"] for p in d["pins"]]))


def add(asset, graph, ntype, x, y, **kw):
    r = bp("add_node", {"asset_path": asset, "graph_name": graph,
                        "node_type": ntype, "position": [x, y], **kw})
    nid = r.get("id") or r.get("node_id")
    if not nid:
        raise RuntimeError("add_node 실패 %s %s -> %s" % (ntype, kw, json.dumps(r)[:400]))
    w("  + %-14s %-22s -> %s" % (ntype, kw.get("function_name") or kw.get("variable_name") or "", nid))
    return nid


def setdef(asset, graph, nid, pin_name, val):
    bp("set_pin_default", {"asset_path": asset, "graph_name": graph,
                           "node_id": nid, "pin_name": pin_name, "value": val})
    w("    def %s.%s = %s" % (nid, pin_name, val))


def conn(asset, graph, sn, sp, tn, tp):
    r = bp("connect_pins", {"asset_path": asset, "graph_name": graph,
                            "source_node": sn, "source_pin": sp,
                            "target_node": tn, "target_pin": tp})
    ok = r.get("success", True)
    w("    %s %s.%s -> %s.%s" % ("OK  " if ok else "FAIL", sn, sp, tn, tp))
    if not ok:
        raise RuntimeError("connect 실패: %s" % json.dumps(r)[:400])


def disc(asset, graph, sn, sp, tn, tp):
    bp("disconnect_pins", {"asset_path": asset, "graph_name": graph,
                           "source_node": sn, "source_pin": sp,
                           "target_node": tn, "target_pin": tp})
    w("    cut  %s.%s -/-> %s.%s" % (sn, sp, tn, tp))


def compile_bp(asset):
    r = bp("compile_blueprint", {"asset_path": asset})
    w("  compile %s : %s" % (asset.rsplit("/", 1)[-1], json.dumps(r, ensure_ascii=False)[:300]))
    return r


def save_bp(asset):
    try:
        r = bp("save_asset", {"asset_path": asset})
        w("  save %s : %s" % (asset.rsplit("/", 1)[-1], json.dumps(r, ensure_ascii=False)[:200]))
        if r.get("saved") or r.get("success"):
            return
    except Exception as e:
        w("  save_asset 예외: %r" % (e,))
    # ⚠ save_packages 파라미터명은 packages (asset_paths 아님)
    r = call("editor_query", "save_packages", {"packages": [asset]})
    w("  save_packages fallback: %s" % json.dumps(r, ensure_ascii=False)[:300])


# ══════════════════════════════════════════════════════════════════
# [A] 골반 스프링 게이트 이징
# ══════════════════════════════════════════════════════════════════
w("=" * 70)
w("[A] PC_01_ABP / LedgeIK — 골반 스프링 게이트 이징")
w("=" * 70)

d_curve = nd(ABP, G_IK, CURVE_GET)
assert d_curve.get("function") == "GetCurveValue", "CF_44 가 GetCurveValue 아님: %s" % d_curve.get("function")
assert pin(d_curve, "CurveName")["default_value"] == "ledge_pelvis_spring", \
    "커브명 상이: %s" % pin(d_curve, "CurveName")["default_value"]
assert pin(d_curve, "ReturnValue")["connected_to"] == ["%s.LedgePelvisSpring" % SPRING_SET], \
    "배선 상이: %s" % pin(d_curve, "ReturnValue")["connected_to"]
w("  preflight ok — GetCurveValue(ledge_pelvis_spring) -> Set LedgePelvisSpring 직결 확인")

ease = add(ABP, G_IK, "CallFunction", 1650, 330, function_name="Ease", target_class=KML)
d_ease = nd(ABP, G_IK, ease)
w("  Ease 핀: %s" % [p["name"] for p in d_ease["pins"]])

setdef(ABP, G_IK, ease, "A", "0.0")
setdef(ABP, G_IK, ease, "B", "1.0")
setdef(ABP, G_IK, ease, "EasingFunc", "SinusoidalInOut")
setdef(ABP, G_IK, ease, "BlendExp", "2.0")

disc(ABP, G_IK, CURVE_GET, "ReturnValue", SPRING_SET, "LedgePelvisSpring")
conn(ABP, G_IK, CURVE_GET, "ReturnValue", ease, "Alpha")
conn(ABP, G_IK, ease, "ReturnValue", SPRING_SET, "LedgePelvisSpring")

# 역추적 검증 (knot 경유 오결선 방지)
src = pin(nd(ABP, G_IK, SPRING_SET), "LedgePelvisSpring")["connected_to"]
assert src == ["%s.ReturnValue" % ease], "Set 입력이 Ease 가 아님: %s" % src
d_ease = nd(ABP, G_IK, ease)
assert pin(d_ease, "Alpha")["connected_to"] == ["%s.ReturnValue" % CURVE_GET], \
    "Ease.Alpha 소스 상이: %s" % pin(d_ease, "Alpha")["connected_to"]
w("  [A] 배선 검증 통과: 커브 -> Ease.Alpha -> Set LedgePelvisSpring")
w("  [A] 이징 파라미터: %s" % {p["name"]: p["default_value"] for p in d_ease["pins"]
                              if p["direction"] == "input" and not p["is_exec"]})

# ══════════════════════════════════════════════════════════════════
# [B-1] LedgeState 에 LedgeLookIdle 출력 추가
# ══════════════════════════════════════════════════════════════════
w("")
w("=" * 70)
w("[B-1] PC_01_ABP / LedgeState — LedgeLookIdle 출력 추가")
w("=" * 70)

sig = bp("get_function_signature", {"blueprint_path": ABP, "function_name": G_STATE})
have = {o["name"] for o in sig["outputs"]}
if "LedgeLookIdle" not in have:
    bp("set_function_params", {"asset_path": ABP, "function_name": G_STATE,
                               "outputs": [{"name": "LedgeLookIdle", "type": "bool"}]})
    w("  출력 LedgeLookIdle(bool) 추가")
else:
    w("  출력 LedgeLookIdle 이미 존재 — 건너뜀")

g_stopped = add(ABP, G_STATE, "VariableGet", -700, 900, variable_name="LedgeStopped")
g_event = add(ABP, G_STATE, "VariableGet", -700, 990, variable_name="bLedgeEventAnim")
n_not = add(ABP, G_STATE, "CallFunction", -460, 985, function_name="Not_PreBool", target_class=KML)
n_and = add(ABP, G_STATE, "CallFunction", -260, 930, function_name="BooleanAND", target_class=KML)

conn(ABP, G_STATE, g_stopped, "LedgeStopped", n_and, "A")
conn(ABP, G_STATE, g_event, "bLedgeEventAnim", n_not, "A")
conn(ABP, G_STATE, n_not, "ReturnValue", n_and, "B")
conn(ABP, G_STATE, n_and, "ReturnValue", STATE_RESULT, "LedgeLookIdle")

src = pin(nd(ABP, G_STATE, STATE_RESULT), "LedgeLookIdle")["connected_to"]
assert src == ["%s.ReturnValue" % n_and], "반환핀 소스 상이: %s" % src
w("  [B-1] LedgeLookIdle = LedgeStopped AND NOT bLedgeEventAnim  배선 확인")

compile_bp(ABP)

# ══════════════════════════════════════════════════════════════════
# [B-2] 레이어 ABP — 변수 + LedgeState 출력 캡처
# ══════════════════════════════════════════════════════════════════
w("")
w("=" * 70)
w("[B-2] PC_01_AnimLayer_Ledge — LedgeLookIdle 변수 + 캡처")
w("=" * 70)

lay_vars = {v["name"] for v in bp("get_variables", {"asset_path": LAY})["variables"]}
if "LedgeLookIdle" not in lay_vars:
    bp("add_variable", {"asset_path": LAY, "name": "LedgeLookIdle", "type": "bool",
                        "default_value": "false", "category": "Custom Move Ledge"})
    w("  레이어 변수 LedgeLookIdle(bool) 추가")
else:
    w("  레이어 변수 LedgeLookIdle 이미 존재 — 건너뜀")

bp("refresh_node", {"asset_path": LAY, "graph_name": LAY_EG, "node_id": LEDGESTATE_CALL})
d_call = nd(LAY, LAY_EG, LEDGESTATE_CALL)
names = [p["name"] for p in d_call["pins"]]
assert "LedgeLookIdle" in names, "LedgeState 콜 노드에 새 출력핀 없음 (refresh 실패): %s" % names
w("  refresh_node ok — 새 출력핀 노출 확인")

# Debug Ledge Seq 직전에 Set 스플라이스
cur = LEDGESTATE_CALL
prev = None
nxt = None
for _ in range(40):
    dcur = nd(LAY, LAY_EG, cur)
    tgt = pin(dcur, "then")["connected_to"]
    assert tgt, "exec 체인 끊김 at %s" % cur
    nid = tgt[0].split(".")[0]
    dn = nd(LAY, LAY_EG, nid)
    if dn.get("function") == "DebugLedgeSeq" or "Debug Ledge Seq" in dn["title"]:
        prev, nxt = cur, nid
        break
    cur = nid
assert prev and nxt, "Debug Ledge Seq 노드를 exec 체인에서 못 찾음"
w("  스플라이스 지점: %s.then -> %s (Debug Ledge Seq)" % (prev, nxt))

set_idle = add(LAY, LAY_EG, "VariableSet", 3020, 112, variable_name="LedgeLookIdle")
disc(LAY, LAY_EG, prev, "then", nxt, "execute")
conn(LAY, LAY_EG, prev, "then", set_idle, "execute")
conn(LAY, LAY_EG, set_idle, "then", nxt, "execute")
conn(LAY, LAY_EG, LEDGESTATE_CALL, "LedgeLookIdle", set_idle, "LedgeLookIdle")

src = pin(nd(LAY, LAY_EG, set_idle), "LedgeLookIdle")["connected_to"]
assert src == ["%s.LedgeLookIdle" % LEDGESTATE_CALL], "Set 입력 소스 상이: %s" % src
w("  [B-2] 캡처 배선 확인")

# ══════════════════════════════════════════════════════════════════
# [B-3] UpdateLedgeLook — AND 체인 합류
# ══════════════════════════════════════════════════════════════════
w("")
w("=" * 70)
w("[B-3] UpdateLedgeLook — Idle 조건 AND 합류")
w("=" * 70)

d_and17 = nd(LAY, G_LOOK, LOOK_AND)
assert pin(d_and17, "ReturnValue")["connected_to"] == ["%s.bPickA" % LOOK_SEL], \
    "기존 배선 상이: %s" % pin(d_and17, "ReturnValue")["connected_to"]

g_idle = add(LAY, G_LOOK, "VariableGet", 880, 600, variable_name="LedgeLookIdle")
and_new = add(LAY, G_LOOK, "CallFunction", 940, 540, function_name="BooleanAND", target_class=KML)

disc(LAY, G_LOOK, LOOK_AND, "ReturnValue", LOOK_SEL, "bPickA")
conn(LAY, G_LOOK, LOOK_AND, "ReturnValue", and_new, "A")
conn(LAY, G_LOOK, g_idle, "LedgeLookIdle", and_new, "B")
conn(LAY, G_LOOK, and_new, "ReturnValue", LOOK_SEL, "bPickA")

src = pin(nd(LAY, G_LOOK, LOOK_SEL), "bPickA")["connected_to"]
assert src == ["%s.ReturnValue" % and_new], "SelectFloat.bPickA 소스 상이: %s" % src
d_new = nd(LAY, G_LOOK, and_new)
assert pin(d_new, "A")["connected_to"] == ["%s.ReturnValue" % LOOK_AND]
assert pin(d_new, "B")["connected_to"] == ["%s.LedgeLookIdle" % g_idle]
w("  [B-3] 배선 검증 통과: (기존 4조건) AND LedgeLookIdle -> SelectFloat.bPickA")

compile_bp(LAY)

# ══════════════════════════════════════════════════════════════════
# 저장
# ══════════════════════════════════════════════════════════════════
w("")
w("=" * 70)
w("저장")
w("=" * 70)
save_bp(ABP)
save_bp(LAY)

w("")
w("신규 노드 요약:")
w("  [A] LedgeIK        Ease=%s" % ease)
w("  [B-1] LedgeState   get=%s/%s not=%s and=%s" % (g_stopped, g_event, n_not, n_and))
w("  [B-2] EventGraph   set=%s (splice %s -> %s)" % (set_idle, prev, nxt))
w("  [B-3] UpdateLook   get=%s and=%s" % (g_idle, and_new))

out = r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\H---------Claude-Sanjuk-Unreal\13217e5f-1fe8-48a4-a44a-f44cb2b73afa\scratchpad\ledge_smooth_pack_0811.log"
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(LOG))
print("\nlog -> " + out)
