# -*- coding: utf-8 -*-
"""LedgeLookIdle 판정 교체 — 프록시 폐기, 블렌드스택 애님 이름 직접 판정 (2026-08-11)

배경: ledge_smooth_pack_0811.py 에서 넣은
  LedgeLookIdle = LedgeStopped AND NOT bLedgeEventAnim
가 Idle 에서도 false 로 나와 시선 AO 가 아예 안 걸림(승호 리포트).

정적 근거:
  - bLedgeEventAnim 은 OnStateEntry_EventMove 에서 true, SetStateMachineBlendStackAnim
    선두에서만 false. 렛지=EventMove 진입이라 세션 내내 true 로 래치될 수 있음
  - LedgeStopped 는 Distance(손월드타깃, LedgePrevWorldNowL) < DeltaTime*15 (≈0.25cm @60fps)
    라는 간접 신호 — 어느 쪽이 죽였든 둘 다 "Idle 애님 재생 중"의 직접 신호가 아님

교체: LedgeLookIdle = Contains(GetObjectName(BlendStackInputs.Anim), "_Idle")
  LedgeClimbing 실측 자산명:
    P_Player_Ledge_Idle / P_Player_Ledge_Idle_Wallless          -> "_Idle" 매치 O
    P_Player_Ledge_MoveToIdle_L/R/_Wallless_L/_Wallless_R       -> "MoveTo|Idle" 이라 매치 X
  즉 언더바 포함 "_Idle" 한 번으로 매달린 Idle 2종만 정확히 잡힌다.
  패턴 출처 = 같은 ABP 의 IsStarting (BlendStackInputs.Tags Contains "Pivot").

⚠ 애님 리네임 시 깨지는 판정이라 그래프에 코멘트 남김.
"""
import json
import urllib.request

MCP = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
LAY = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_AnimLayer_Ledge"
G = "LedgeState"
RESULT = "K2Node_FunctionResult_0"
KSL = "KismetSystemLibrary"
KSTR = "KismetStringLibrary"

# ledge_smooth_pack_0811.py 가 만든 폐기 대상
OLD = ["K2Node_VariableGet_5", "K2Node_VariableGet_6",
       "K2Node_CallFunction_0", "K2Node_CallFunction_1"]

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


def bp(a, p, t=300):
    return call("blueprint_query", a, p, t)


def nd(nid, graph=G, asset=ABP):
    return bp("get_node_details", {"asset_path": asset, "graph_name": graph, "node_id": nid})


def pin(d, name):
    for p in d["pins"]:
        if p["name"] == name:
            return p
    raise KeyError("pin %s 없음 in %s: %s" % (name, d["id"], [p["name"] for p in d["pins"]]))


def add(ntype, x, y, **kw):
    r = bp("add_node", {"asset_path": ABP, "graph_name": G, "node_type": ntype,
                        "position": [x, y], **kw})
    nid = r.get("id") or r.get("node_id")
    if not nid:
        raise RuntimeError("add_node 실패 %s %s -> %s" % (ntype, kw, json.dumps(r)[:400]))
    w("  + %-13s %-22s -> %s" % (ntype, kw.get("function_name") or kw.get("variable_name")
                                 or kw.get("struct_type") or "", nid))
    return nid


def conn(sn, sp, tn, tp):
    r = bp("connect_pins", {"asset_path": ABP, "graph_name": G,
                            "source_node": sn, "source_pin": sp,
                            "target_node": tn, "target_pin": tp})
    ok = r.get("success", True)
    w("    %s %s.%s -> %s.%s" % ("OK  " if ok else "FAIL", sn, sp, tn, tp))
    if not ok:
        raise RuntimeError("connect 실패: %s" % json.dumps(r)[:400])


w("=" * 70)
w("LedgeState / LedgeLookIdle 판정 교체")
w("=" * 70)

# ── 0) PIE 중이면 remove_node 크래시 위험 → 사전 확인 ────────────────
try:
    call("editor_query", "pie_get_object_properties",
         {"class_name": "SBCharacter", "anim_instance": True, "properties": ["LedgeStopped"]})
    raise SystemExit("!! PIE 가 실행 중으로 보인다. remove_node 는 PIE 중 크래시 이력 있음 — PIE 종료 후 재실행할 것")
except RuntimeError as e:
    if "PIE" not in str(e) and "matched" not in str(e):
        raise
    w("  PIE 미실행 확인 (remove_node 안전)")

# ── 1) 신규 판정 체인 ────────────────────────────────────────────────
g_bsi = add("VariableGet", -1180, 1180, variable_name="BlendStackInputs")
brk = add("BreakStruct", -960, 1180, struct_type="S_BlendStackInputs")

d_brk = nd(brk)
anim_pin = next(p["name"] for p in d_brk["pins"]
                if p["direction"] == "output" and p["name"].startswith("Anim"))
w("  BreakStruct Anim 핀명: %s" % anim_pin)

conn(g_bsi, "BlendStackInputs", brk, "S_BlendStackInputs")

n_name = add("CallFunction", -680, 1180, function_name="GetObjectName", target_class=KSL)
n_has = add("CallFunction", -420, 1180, function_name="Contains", target_class=KSTR)
w("  Contains 핀: %s" % [p["name"] for p in nd(n_has)["pins"]])

conn(brk, anim_pin, n_name, "Object")
conn(n_name, "ReturnValue", n_has, "SearchIn")
bp("set_pin_default", {"asset_path": ABP, "graph_name": G, "node_id": n_has,
                       "pin_name": "Substring", "value": "_Idle"})
w("    def %s.Substring = _Idle" % n_has)

conn(n_has, "ReturnValue", RESULT, "LedgeLookIdle")

src = pin(nd(RESULT), "LedgeLookIdle")["connected_to"]
assert src == ["%s.ReturnValue" % n_has], "반환핀 소스 상이: %s" % src
w("  신규 배선 검증 통과")

# ── 2) 구 프록시 체인 제거 ───────────────────────────────────────────
for nid in OLD:
    try:
        d = nd(nid)
    except RuntimeError:
        w("  (없음) %s" % nid)
        continue
    title = d["title"].replace("\n", " / ")
    bp("remove_node", {"asset_path": ABP, "graph_name": G, "node_id": nid})
    w("  - 제거 %s [%s]" % (nid, title))

# ── 3) 코멘트 ────────────────────────────────────────────────────────
try:
    bp("add_comment_node", {"asset_path": ABP, "graph_name": G,
                            "position": [-1220, 1100], "size": [900, 200],
                            "text": "LedgeLookIdle = 시선 AO 게이트 (UpdateLedgeLook 에서 AND).\n"
                                    "현재 블렌드스택 애님 이름에 \"_Idle\" 포함 여부로 판정 = 매달린 Idle 2종\n"
                                    "(P_Player_Ledge_Idle / _Idle_Wallless). MoveToIdle 4종은 \"MoveTo|Idle\" 이라 제외됨.\n"
                                    "!! 애님 리네임 시 이 문자열 같이 고칠 것. 2026-08-11"})
    w("  코멘트 추가")
except Exception as e:
    w("  코멘트 실패(무시): %r" % (e,))

# ── 4) 컴파일 + 저장 ─────────────────────────────────────────────────
r = bp("compile_blueprint", {"asset_path": ABP})
w("  compile: success=%s errors=%s" % (r.get("success"), r.get("error_count")))
assert r.get("error_count", 1) == 0, "컴파일 에러: %s" % json.dumps(r.get("errors"))[:500]

r = bp("save_asset", {"asset_path": ABP})
w("  save: %s" % json.dumps(r, ensure_ascii=False)[:200])

# ── 5) 최종 확인 ─────────────────────────────────────────────────────
w("")
w("최종 LedgeState 판정 체인:")
w("  BlendStackInputs -> Break.%s -> GetObjectName -> Contains(\"_Idle\") -> LedgeLookIdle" % anim_pin)
sig = bp("get_function_signature", {"blueprint_path": ABP, "function_name": G})
w("  LedgeState 출력 %d개 (LedgeLookIdle 포함=%s)"
  % (len(sig["outputs"]), any(o["name"] == "LedgeLookIdle" for o in sig["outputs"])))
w("  레이어측(변수 캡처 + UpdateLedgeLook AND) 은 변경 없음 — 그대로 유효")

out = (r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\H---------Claude-Sanjuk-Unreal"
       r"\13217e5f-1fe8-48a4-a44a-f44cb2b73afa\scratchpad\ledge_lookidle_fix_0811.log")
with open(out, "w", encoding="utf-8") as f:
    f.write("\n".join(LOG))
print("\nlog -> " + out)
