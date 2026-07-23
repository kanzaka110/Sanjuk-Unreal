# Phase C M1c — sd/td 래치 소스를 신선한 함수 파라미터로 교체 (2026-07-23)
# 문제: Break(ABP var LedgeMoveData)는 한 틱 스테일 → Td에지 프레임에 직전 이동 sd/td가 래치됨
#       (실측: cur 693~748 이동 중 래치 sd/td=499/629 = 직전 구간)
# 수정: setTd ← Entry.Td(=CF_211에 물린 엔트리 핀), setSd ← Entry.Current(=Td−Current Subtract의 상대 핀),
#       xt.Distance ← 동일 Current. Break 노드는 연결만 해제(노드 보존).
# 실행: py phase_c_m1c_fresh.py [apply]
import json, sys, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GH = "Ledge_HandTarget"
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"

TD_EDGE = "K2Node_CallFunction_211"
BRK = "K2Node_BreakStruct_0"
XT = "K2Node_CallFunction_114"
SETSD = "K2Node_VariableSet_10"
SETTD = "K2Node_VariableSet_11"


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:400])
    return json.loads(txt)


def bq(action, params):
    p = {"asset_path": ABP}
    p.update(params)
    return call("blueprint_query", action, p)


def pie_on():
    r = call("editor_query", "run_python", {
        "command": "import unreal;print(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None)",
        "mode": "execute_file"})
    return "True" in json.dumps(r.get("output", []))


nodes = {n["id"]: n for n in bq("get_graph_data", {"graph_name": GH})["nodes"]}


def pinmap(nid):
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


entry = next(nid for nid, n in nodes.items() if n["class"] == "K2Node_FunctionEntry")

# Td 핀: CF_211 입력 중 엔트리에서 오는 것
td_pin = None
for p in nodes[TD_EDGE]["pins"]:
    if p["direction"] == "input":
        for c in p.get("connected_to", []):
            cn, cp = c.rsplit(".", 1)
            if cn == entry:
                td_pin = cp
assert td_pin, "CF_211에 엔트리 직결 핀 없음"

# Current 핀: 엔트리 Td핀과 다른 엔트리 핀을 입력으로 갖는 Subtract
cur_pin = None
sub_id = None
for nid, n in nodes.items():
    if n["class"] != "K2Node_CallFunction" or "Subtract_Double" not in str(n.get("function")):
        continue
    srcs = []
    for p in n.get("pins", []):
        if p["direction"] == "input":
            for c in p.get("connected_to", []):
                cn, cp = c.rsplit(".", 1)
                if cn == entry:
                    srcs.append(cp)
    if td_pin in srcs and len(srcs) == 2:
        sub_id = nid
        cur_pin = next(s for s in srcs if s != td_pin)
assert cur_pin, "Td−Current Subtract 미발견"
print("[PF] entry =", entry, "| Td pin =", td_pin, "| Current pin =", cur_pin, "(sub:", sub_id + ")")

# 현 배선 확인
sd_src = [c for p in nodes[SETSD]["pins"] if p["name"] == "LedgeMoveStartDist" and p["direction"] == "input"
          for c in p.get("connected_to", [])]
td_src = [c for p in nodes[SETTD]["pins"] if p["name"] == "LedgeMoveTargetDist" and p["direction"] == "input"
          for c in p.get("connected_to", [])]
print("[PF] setSd src =", sd_src, "| setTd src =", td_src)
assert sd_src == [BRK + ".UnitMoveStartDistance"], "setSd 소스 상이"
assert td_src == [BRK + ".UnitMoveTargetDistance"], "setTd 소스 상이"

if not APPLY:
    print("== DRY-RUN OK ==")
    sys.exit(0)

assert not pie_on(), "PIE 실행 중 — 종료 후 apply"


def disc(sn, sp, tn, tp):
    bq("disconnect_pins", {"graph_name": GH, "source_node": sn, "source_pin": sp,
                           "target_node": tn, "target_pin": tp})
    print("[DISC]", sn + "." + sp, "x", tn + "." + tp)


def wire(sn, sp, tn, tp):
    bq("connect_pins", {"graph_name": GH, "source_node": sn, "source_pin": sp,
                        "target_node": tn, "target_pin": tp})
    print("[WIRE]", sn + "." + sp, "->", tn + "." + tp)


disc(BRK, "UnitMoveStartDistance", SETSD, "LedgeMoveStartDist")
disc(BRK, "UnitMoveTargetDistance", SETTD, "LedgeMoveTargetDist")
disc(BRK, "UnitMoveStartDistance", XT, "Distance")
wire(entry, cur_pin, SETSD, "LedgeMoveStartDist")
wire(entry, td_pin, SETTD, "LedgeMoveTargetDist")
wire(entry, cur_pin, XT, "Distance")

# 검증
nodes = {n["id"]: n for n in bq("get_graph_data", {"graph_name": GH})["nodes"]}
ok = True
for tgt, pin, want in [(SETSD, "LedgeMoveStartDist", entry + "." + cur_pin),
                       (SETTD, "LedgeMoveTargetDist", entry + "." + td_pin),
                       (XT, "Distance", entry + "." + cur_pin)]:
    got = [c for p in nodes[tgt]["pins"] if p["name"] == pin and p["direction"] == "input"
           for c in p.get("connected_to", [])]
    if got != [want]:
        print("!! ", tgt, pin, "=", got, "expected", want)
        ok = False
if not ok:
    sys.exit(1)
print("[VERIFY] 재배선 확인")
r = bq("compile_blueprint", {})
print("[COMPILE]", json.dumps(r, ensure_ascii=False)[:200])
