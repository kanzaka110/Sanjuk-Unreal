# 렛지 정리 2차 (2026-07-25) — LineSnap 절대 스냅 도입으로 무효화된 잔재 제거 (기능 유지)
# ①HandTarget 구 라이브Dz 주입 스플라이스 제거 ②SlopeZ K체인+DzL/R Set+Hold 제거
# ③ProcWindow 기각시도② 5노드 ④LedgeDebugs 죽은 24노드 ⑤변수 4종
# 유지: DzBody 체인, LineSnap 2회 호출, ProcWin 창, MoveFloor, LedgeUnitMoving
# 실행: py cleanup2_apply.py         (사전 점검)
#       py cleanup2_apply.py apply   (적용)
import json
import sys
import urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"

HT = "Ledge_HandTarget"
SZ = "Ledge_SlopeZ"
PW = "Ledge_ProcWindow"
DB = "LedgeDebugs"

# HandTarget 스플라이스: (A소스, A핀, Add노드, 소비노드, 소비핀) + 삭제 노드
HT_SPLICE = [
    ("K2Node_CallFunction_55", "ReturnValue", "K2Node_CallFunction_188", "K2Node_CallFunction_115", "Target"),
    ("K2Node_CallFunction_91", "ReturnValue", "K2Node_CallFunction_190", "K2Node_CallFunction_177", "Target"),
]
HT_DEL = ["K2Node_CallFunction_188", "K2Node_CallFunction_187", "K2Node_VariableGet_50",
          "K2Node_CallFunction_190", "K2Node_CallFunction_189", "K2Node_VariableGet_61",
          "K2Node_VariableGet_85", "K2Node_VariableGet_86"]

# SlopeZ exec 스플라이스: then IfThenElse_0.then→Set_2 / else IfThenElse_0.else→Set_5 / Set_5.then→(끊음)
SZ_DEL = ["K2Node_VariableSet_0", "K2Node_VariableSet_1", "K2Node_VariableSet_3", "K2Node_VariableSet_4",
          "K2Node_VariableSet_6", "K2Node_VariableSet_7", "K2Node_VariableSet_8", "K2Node_VariableSet_9",
          "K2Node_IfThenElse_1", "K2Node_VariableGet_5",
          "K2Node_CallFunction_29", "K2Node_CallFunction_30", "K2Node_CallFunction_31", "K2Node_CallFunction_32",
          "K2Node_CallFunction_33", "K2Node_CallFunction_34", "K2Node_CallFunction_35", "K2Node_CallFunction_36",
          "K2Node_CallFunction_37", "K2Node_CallFunction_38"]

PW_DEL = ["K2Node_CallFunction_30", "K2Node_CallFunction_31", "K2Node_CallFunction_32",
          "K2Node_CallFunction_33", "K2Node_CallFunction_35"]

DB_DEL = ["K2Node_BreakStruct_2", "K2Node_CallFunction_106", "K2Node_CallFunction_107", "K2Node_CallFunction_108",
          "K2Node_CallFunction_29", "K2Node_CallFunction_6", "K2Node_CallFunction_65", "K2Node_CallFunction_7",
          "K2Node_CallFunction_85", "K2Node_CallFunction_90", "K2Node_FormatText_7", "K2Node_PromotableOperator_14",
          "K2Node_PromotableOperator_15", "K2Node_VariableGet_10", "K2Node_VariableGet_12", "K2Node_VariableGet_15",
          "K2Node_VariableGet_3", "K2Node_VariableGet_63", "K2Node_VariableGet_66", "K2Node_VariableGet_7",
          "K2Node_VariableGet_76", "K2Node_VariableGet_8", "K2Node_VariableSet_1", "K2Node_VariableSet_7"]

DEL_VARS = ["LedgeSlopeDzHoldL", "LedgeSlopeDzHoldR", "LedgeSlopeDzL", "LedgeSlopeDzR"]


def call(tool: str, action: str, params: dict, timeout: int = 300) -> dict:
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:400])
    return json.loads(txt)


def bq(action: str, params: dict) -> dict:
    p = {"asset_path": ABP}
    p.update(params)
    return call("blueprint_query", action, p)


def graph(g: str) -> dict:
    return {n["id"]: n for n in bq("get_graph_data", {"graph_name": g})["nodes"]}


def pins(nodes: dict, nid: str) -> dict:
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


def pie_on() -> bool:
    r = call("editor_query", "run_python", {
        "command": "import unreal;print(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None)",
        "mode": "execute_file"})
    return "True" in json.dumps(r.get("output", []))


# ── 사전 점검 ──
ht = graph(HT)
sz = graph(SZ)
checks = []
for a, ap, add_n, cons, cp in HT_SPLICE:
    checks.append((pins(ht, cons)[cp]["connected_to"] == [add_n + ".ReturnValue"], f"HT {cons}.{cp} ← {add_n}"))
    checks.append((pins(ht, add_n)["A"]["connected_to"] == [a + "." + ap], f"HT {add_n}.A ← {a}"))
checks.append((pins(sz, "K2Node_VariableSet_2")["execute"]["connected_to"] == ["K2Node_VariableSet_1.then"], "SZ Set_2(DzBody).exec ← Set_1.then"))
checks.append((pins(sz, "K2Node_VariableSet_5")["execute"]["connected_to"] == ["K2Node_VariableSet_4.then"], "SZ Set_5(DzBody0).exec ← Set_4.then"))
checks.append((pins(sz, "K2Node_VariableSet_0")["execute"]["connected_to"] == ["K2Node_IfThenElse_0.then"], "SZ Set_0.exec ← 게이트.then"))
checks.append((pins(sz, "K2Node_VariableSet_3")["execute"]["connected_to"] == ["K2Node_IfThenElse_0.else"], "SZ Set_3.exec ← 게이트.else"))
ok = True
for good, label in checks:
    print("[PF]", "OK " if good else "FAIL", label)
    ok = ok and good
if not APPLY:
    print("[PF] 사전 점검", "통과 — apply로 실행" if ok else "실패")
    sys.exit(0 if ok else 1)
assert ok, "사전 점검 실패"
assert not pie_on(), "PIE 실행 중 — 종료 후 재실행"

# ── 1) HandTarget 스플라이스 + 삭제 ──
for a, ap, add_n, cons, cp in HT_SPLICE:
    bq("disconnect_pins", {"graph_name": HT, "source_node": add_n, "source_pin": "ReturnValue",
                           "target_node": cons, "target_pin": cp})
    bq("connect_pins", {"graph_name": HT, "source_node": a, "source_pin": ap,
                        "target_node": cons, "target_pin": cp})
    print("[HT] 스플라이스", a, "→", cons)
for nid in HT_DEL:
    try:
        bq("remove_node", {"graph_name": HT, "node_id": nid})
    except RuntimeError as e:
        print("[HT] remove 실패", nid, str(e)[:80])
print("[HT] 삭제", len(HT_DEL))

# ── 2) SlopeZ exec 스플라이스 + 삭제 ──
bq("disconnect_pins", {"graph_name": SZ, "source_node": "K2Node_IfThenElse_0", "source_pin": "then",
                       "target_node": "K2Node_VariableSet_0", "target_pin": "execute"})
bq("connect_pins", {"graph_name": SZ, "source_node": "K2Node_IfThenElse_0", "source_pin": "then",
                    "target_node": "K2Node_VariableSet_2", "target_pin": "execute"})
bq("disconnect_pins", {"graph_name": SZ, "source_node": "K2Node_IfThenElse_0", "source_pin": "else",
                       "target_node": "K2Node_VariableSet_3", "target_pin": "execute"})
bq("connect_pins", {"graph_name": SZ, "source_node": "K2Node_IfThenElse_0", "source_pin": "else",
                    "target_node": "K2Node_VariableSet_5", "target_pin": "execute"})
for nid in SZ_DEL:
    try:
        bq("remove_node", {"graph_name": SZ, "node_id": nid})
    except RuntimeError as e:
        print("[SZ] remove 실패", nid, str(e)[:80])
print("[SZ] 삭제", len(SZ_DEL))

# ── 3) ProcWindow / LedgeDebugs 삭제 ──
for g, dels in ((PW, PW_DEL), (DB, DB_DEL)):
    for nid in dels:
        try:
            bq("remove_node", {"graph_name": g, "node_id": nid})
        except RuntimeError as e:
            print(f"[{g}] remove 실패", nid, str(e)[:80])
    print(f"[{g}] 삭제", len(dels))

# ── 4) 컴파일 → 변수 삭제 → 재컴파일 ──
r = bq("compile_blueprint", {})
print("[COMPILE-1]", json.dumps(r)[:150])
for v in DEL_VARS:
    try:
        bq("remove_variable", {"name": v})
        print("[VAR] -", v)
    except RuntimeError as e:
        print("[VAR] 삭제 실패", v, str(e)[:100])
r = bq("compile_blueprint", {})
print("[COMPILE-2]", json.dumps(r)[:200])

# ── 5) 검증 ──
ht2 = graph(HT)
sz2 = graph(SZ)
pw2 = graph(PW)
db2 = graph(DB)
v = []
v.append((pins(ht2, "K2Node_CallFunction_115")["Target"]["connected_to"] == ["K2Node_CallFunction_55.ReturnValue"], "HT L Target ← CF_55 직결"))
v.append((pins(ht2, "K2Node_CallFunction_177")["Target"]["connected_to"] == ["K2Node_CallFunction_91.ReturnValue"], "HT R Target ← CF_91 직결"))
v.append((all(n not in ht2 for n in HT_DEL), "HT 8노드 제거"))
v.append((pins(sz2, "K2Node_VariableSet_2")["execute"]["connected_to"] == ["K2Node_IfThenElse_0.then"], "SZ then → DzBody 직결"))
v.append((pins(sz2, "K2Node_VariableSet_5")["execute"]["connected_to"] == ["K2Node_IfThenElse_0.else"], "SZ else → DzBody0 직결"))
v.append((all(n not in sz2 for n in SZ_DEL), "SZ 20노드 제거"))
v.append((all(n not in pw2 for n in PW_DEL), "PW 5노드 제거"))
v.append((all(n not in db2 for n in DB_DEL), "DB 24노드 제거"))
vars_now = {x["name"] for x in bq("get_variables", {}).get("variables", [])}
v.append((not (set(DEL_VARS) & vars_now), "변수 4종 제거"))
allok = True
for good, label in v:
    print("[CHK]", "OK " if good else "FAIL", label)
    allok = allok and good
print("[SIZE] HT", len(ht2), "SZ", len(sz2), "PW", len(pw2), "DB", len(db2), "vars", len(vars_now))
assert allok, "검증 실패"
print("[DONE] 정리 완료 — PIE 회귀 확인 대기")
