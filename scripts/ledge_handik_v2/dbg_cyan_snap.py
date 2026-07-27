# LedgeDebugs 정리 (2026-07-25) — 노랑 구체 제거 + 시안 구체 라인 Z 스냅
# 시안(다음 도착 앵커 프리뷰) = (앵커+UnitMoveVec) XY 유지, Z = 스플라인최근접Z + C0 절대 스냅
# 스플라인 무효 시 시안 드로우 스킵 (Branch else → 다음 섹션 직행)
# 실행: py dbg_cyan_snap.py         (사전 점검)
#       py dbg_cyan_snap.py apply   (적용)
import json
import sys
import urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
G = "LedgeDebugs"
KML = "KismetMathLibrary"
KSL = "KismetSystemLibrary"
SPL = "SplineComponent"
C0 = {"L": "-8.66", "R": "-8.79"}
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"

# 기존 노드 (2026-07-25 실측)
YEL = ["K2Node_CallFunction_5", "K2Node_CallFunction_8"]        # 노랑 드로우
YEL_SRC = ["K2Node_CallFunction_1", "K2Node_CallFunction_2"]    # 노랑 중심 계산
CYAN = {"L": "K2Node_CallFunction_32", "R": "K2Node_CallFunction_33"}  # 시안 드로우
DEST = {"L": "K2Node_CallFunction_3", "R": "K2Node_CallFunction_4"}    # 앵커±벡터 (유지)
PREV = ("K2Node_CallFunction_31", "then")   # 노랑 앞 exec
NEXT = ("K2Node_CallFunction_88", "execute")  # 시안 뒤 exec


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


def graph() -> dict:
    return {n["id"]: n for n in bq("get_graph_data", {"graph_name": G})["nodes"]}


def pins(nodes: dict, nid: str) -> dict:
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


def pie_on() -> bool:
    r = call("editor_query", "run_python", {
        "command": "import unreal;print(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None)",
        "mode": "execute_file"})
    return "True" in json.dumps(r.get("output", []))


g = graph()
checks = [
    (pins(g, YEL[0])["execute"]["connected_to"] == [PREV[0] + "." + PREV[1]], "노랑1.exec ← CF_31.then"),
    (pins(g, CYAN["L"])["execute"]["connected_to"] == [YEL[1] + ".then"], "시안L.exec ← 노랑2.then"),
    (pins(g, CYAN["R"])["execute"]["connected_to"] == [CYAN["L"] + ".then"], "시안R.exec ← 시안L.then"),
    (pins(g, NEXT[0])["execute"]["connected_to"] == [CYAN["R"] + ".then"], "다음섹션.exec ← 시안R.then"),
    (pins(g, CYAN["L"])["Center"]["connected_to"] == [DEST["L"] + ".ReturnValue"], "시안L.Center ← CF_3"),
    (pins(g, CYAN["R"])["Center"]["connected_to"] == [DEST["R"] + ".ReturnValue"], "시안R.Center ← CF_4"),
]
ok = True
for good, label in checks:
    print("[PF]", "OK " if good else "FAIL", label)
    ok = ok and good
if not APPLY:
    print("[PF] 사전 점검", "통과 — apply로 실행" if ok else "실패")
    sys.exit(0 if ok else 1)
assert ok, "사전 점검 실패"
assert not pie_on(), "PIE 실행 중 — 종료 후 재실행"

made = {}


def add(key: str, ntype: str, extra: dict, pos: list) -> str:
    p = {"graph_name": G, "node_type": ntype, "position": pos}
    p.update(extra)
    r = bq("add_node", p)
    nid = r.get("id") or r.get("node_id")
    made[key] = nid
    return nid


def wire(sk: str, sp: str, tk: str, tp: str) -> None:
    bq("connect_pins", {"graph_name": G,
                        "source_node": made.get(sk, sk), "source_pin": sp,
                        "target_node": made.get(tk, tk), "target_pin": tp})


def unwire(sk: str, sp: str, tk: str, tp: str) -> None:
    bq("disconnect_pins", {"graph_name": G,
                           "source_node": made.get(sk, sk), "source_pin": sp,
                           "target_node": made.get(tk, tk), "target_pin": tp})


X, Y = -2000, 2600
# ── 1) 게이트 ──
add("getSp", "VariableGet", {"variable_name": "LedgeSplineRef"}, [X, Y - 200])
add("isv", "CallFunction", {"function_class": KSL, "function_name": "IsValid"}, [X + 180, Y - 200])
add("br", "Branch", {}, [X + 360, Y - 200])
wire("getSp", "LedgeSplineRef", "isv", "Object")
wire("isv", "ReturnValue", "br", "Condition")

# ── 2) 손별 스냅 중심 ──
for i, s in enumerate(("L", "R")):
    yo = Y + i * 300
    add("cls" + s, "CallFunction", {"function_class": SPL, "function_name": "FindLocationClosestToWorldLocation"}, [X + 250, yo])
    add("bkC" + s, "CallFunction", {"function_class": KML, "function_name": "BreakVector"}, [X + 500, yo])
    add("c0" + s, "CallFunction", {"function_class": KML, "function_name": "Add_DoubleDouble"}, [X + 660, yo])
    add("bkD" + s, "CallFunction", {"function_class": KML, "function_name": "BreakVector"}, [X + 500, yo + 130])
    add("mk" + s, "CallFunction", {"function_class": KML, "function_name": "MakeVector"}, [X + 840, yo])
    bq("set_pin_default", {"graph_name": G, "node_id": made["cls" + s], "pin_name": "CoordinateSpace", "value": "World"})
    bq("set_pin_default", {"graph_name": G, "node_id": made["c0" + s], "pin_name": "B", "value": C0[s]})
    wire("getSp", "LedgeSplineRef", "cls" + s, "self")
    wire(DEST[s], "ReturnValue", "cls" + s, "WorldLocation")
    wire(DEST[s], "ReturnValue", "bkD" + s, "InVec")
    wire("cls" + s, "ReturnValue", "bkC" + s, "InVec")
    wire("bkC" + s, "Z", "c0" + s, "A")
    wire("bkD" + s, "X", "mk" + s, "X")
    wire("bkD" + s, "Y", "mk" + s, "Y")
    wire("c0" + s, "ReturnValue", "mk" + s, "Z")
    # Center 교체
    unwire(DEST[s], "ReturnValue", CYAN[s], "Center")
    wire("mk" + s, "ReturnValue", CYAN[s], "Center")
print("[G] 스냅 중심 배선 완료")

# ── 3) exec 재배선: PREV → br / br.then → 시안L / br.else → NEXT / (노랑 우회) ──
unwire(PREV[0], PREV[1], YEL[0], "execute")
unwire(YEL[1], "then", CYAN["L"], "execute")
wire(PREV[0], PREV[1], "br", "execute")
wire("br", "then", CYAN["L"], "execute")
wire("br", "else", NEXT[0], NEXT[1])

# ── 4) 노랑 제거 ──
for nid in YEL + YEL_SRC:
    try:
        bq("remove_node", {"graph_name": G, "node_id": nid})
        print("[DEL]", nid)
    except RuntimeError as e:
        print("[DEL] 실패", nid, str(e)[:100])

# ── 5) 컴파일 + 검증 ──
r = bq("compile_blueprint", {})
print("[COMPILE]", json.dumps(r)[:200])

g2 = graph()
v = []
for s in ("L", "R"):
    v.append((pins(g2, CYAN[s])["Center"]["connected_to"] == [made["mk" + s] + ".ReturnValue"], f"시안{s}.Center ← MakeVector(스냅)"))
    v.append((pins(g2, made["cls" + s])["WorldLocation"]["connected_to"] == [DEST[s] + ".ReturnValue"], f"cls{s} ← 원 dest"))
v.append((pins(g2, CYAN["L"])["execute"]["connected_to"] == [made["br"] + ".then"], "시안L.exec ← br.then"))
v.append((sorted(pins(g2, NEXT[0])["execute"]["connected_to"]) == sorted([CYAN["R"] + ".then", made["br"] + ".else"]), "다음섹션 ← 시안R.then + br.else"))
v.append((all(nid not in g2 for nid in YEL + YEL_SRC), "노랑 4노드 제거됨"))
allok = True
for good, label in v:
    print("[CHK]", "OK " if good else "FAIL", label)
    allok = allok and good
assert allok, "링크 검증 실패"
print("[DONE] 노랑 제거 + 시안 라인 스냅 — PIE 육안 확인 대기")
