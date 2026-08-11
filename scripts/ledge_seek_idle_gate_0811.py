# -*- coding: utf-8 -*-
"""LedgeSeek 도 Idle 한정 게이트 (2026-08-11)

UpdateLedgeSeek 의 발동 조건 종단부에 LedgeLookIdle 을 AND 로 합류.
  before: AND[CF_16] -> SelectFloat[CF_23].bPickA -> FInterpTo(10) -> Set LedgeSeekAlpha
  after : AND[CF_16] -> AND[신규].A
          LedgeLookIdle -> AND[신규].B
          AND[신규] -> SelectFloat[CF_23].bPickA

LedgeLookIdle 은 ledge_lookidle_fix_0811.py 로 이미
  Contains(GetObjectName(BlendStackInputs.Anim), "_Idle")
로 교체됐고 EventGraph 에서 매 틱 캡처된다. 시선(UpdateLedgeLook)과 동일 신호 공유.

시킹 BS 도 시선 BS 와 같은 전신 애님 계열이라 Idle 밖에서 걸리면
원본 렛지 애님이 lerp 로 갈려나가는 것은 동일한 문제.
"""
import json
import urllib.request

MCP = "http://localhost:9316/mcp"
LAY = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge"
G = "UpdateLedgeSeek"
KML = "KismetMathLibrary"

SEEK_AND = "K2Node_CallFunction_16"   # 기존 마지막 AND
SEEK_SEL = "K2Node_CallFunction_23"   # SelectFloat(bPickA)

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


def bp(a, p):
    return call("blueprint_query", a, p)


def nd(nid):
    return bp("get_node_details", {"asset_path": LAY, "graph_name": G, "node_id": nid})


def pin(d, name):
    for p in d["pins"]:
        if p["name"] == name:
            return p
    raise KeyError("pin %s 없음 in %s: %s" % (name, d["id"], [p["name"] for p in d["pins"]]))


def add(ntype, x, y, **kw):
    r = bp("add_node", {"asset_path": LAY, "graph_name": G, "node_type": ntype,
                        "position": [x, y], **kw})
    nid = r.get("id") or r.get("node_id")
    if not nid:
        raise RuntimeError("add_node 실패: %s" % json.dumps(r)[:400])
    w("  + %-13s %-18s -> %s" % (ntype, kw.get("function_name") or kw.get("variable_name") or "", nid))
    return nid


def conn(sn, sp, tn, tp):
    r = bp("connect_pins", {"asset_path": LAY, "graph_name": G,
                            "source_node": sn, "source_pin": sp,
                            "target_node": tn, "target_pin": tp})
    ok = r.get("success", True)
    w("    %s %s.%s -> %s.%s" % ("OK  " if ok else "FAIL", sn, sp, tn, tp))
    if not ok:
        raise RuntimeError("connect 실패: %s" % json.dumps(r)[:400])


w("=" * 70)
w("UpdateLedgeSeek — Idle 한정 게이트")
w("=" * 70)

# 프리플라이트
d_and = nd(SEEK_AND)
assert d_and.get("function") == "BooleanAND", "CF_16 이 AND 아님: %s" % d_and.get("function")
assert pin(d_and, "ReturnValue")["connected_to"] == ["%s.bPickA" % SEEK_SEL], \
    "기존 배선 상이: %s" % pin(d_and, "ReturnValue")["connected_to"]
d_sel = nd(SEEK_SEL)
assert pin(d_sel, "A")["default_value"] == "1.0" and pin(d_sel, "B")["default_value"] == "0.0", \
    "SelectFloat 기본값 상이"
lay_vars = {v["name"] for v in bp("get_variables", {"asset_path": LAY})["variables"]}
assert "LedgeLookIdle" in lay_vars, "레이어에 LedgeLookIdle 변수 없음 — 선행 스크립트 확인"
w("  preflight ok — AND[CF_16] -> SelectFloat[CF_23].bPickA / LedgeLookIdle 변수 존재")

# 배선
g_idle = add("VariableGet", 600, 640, variable_name="LedgeLookIdle")
and_new = add("CallFunction", 800, 580, function_name="BooleanAND", target_class=KML)

bp("disconnect_pins", {"asset_path": LAY, "graph_name": G,
                       "source_node": SEEK_AND, "source_pin": "ReturnValue",
                       "target_node": SEEK_SEL, "target_pin": "bPickA"})
w("    cut  %s.ReturnValue -/-> %s.bPickA" % (SEEK_AND, SEEK_SEL))

conn(SEEK_AND, "ReturnValue", and_new, "A")
conn(g_idle, "LedgeLookIdle", and_new, "B")
conn(and_new, "ReturnValue", SEEK_SEL, "bPickA")

# 역추적 검증 (knot 경유 오결선 방지)
src = pin(nd(SEEK_SEL), "bPickA")["connected_to"]
assert src == ["%s.ReturnValue" % and_new], "bPickA 소스 상이: %s" % src
d_new = nd(and_new)
assert pin(d_new, "A")["connected_to"] == ["%s.ReturnValue" % SEEK_AND], \
    "신규 AND.A 소스 상이: %s" % pin(d_new, "A")["connected_to"]
assert pin(d_new, "B")["connected_to"] == ["%s.LedgeLookIdle" % g_idle], \
    "신규 AND.B 소스 상이: %s" % pin(d_new, "B")["connected_to"]
w("  배선 검증 통과: (기존 조건) AND LedgeLookIdle -> SelectFloat.bPickA")

# 컴파일 + 저장
r = bp("compile_blueprint", {"asset_path": LAY})
w("  compile: success=%s errors=%s" % (r.get("success"), r.get("error_count")))
assert r.get("error_count", 1) == 0, "컴파일 에러: %s" % json.dumps(r.get("errors"))[:500]

r = bp("save_asset", {"asset_path": LAY})
w("  save: %s" % json.dumps(r, ensure_ascii=False)[:200])
assert r.get("saved"), "저장 실패"

w("")
w("신규 노드: get=%s and=%s" % (g_idle, and_new))
w("시선(UpdateLedgeLook)/시킹(UpdateLedgeSeek) 둘 다 LedgeLookIdle 공유")

out = (r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\H---------Claude-Sanjuk-Unreal"
       r"\13217e5f-1fe8-48a4-a44a-f44cb2b73afa\scratchpad\ledge_seek_idle_gate_0811.log")
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(LOG))
print("\nlog -> " + out)
