# LineSnap K과장 추가 (2026-07-25) — 라인 정확 스냅은 차등 2.9cm라 시각 인지 불가
# SlopeZ와 동일: mean=(dzL+dzR)/2 보존, 편차 ×3, 후단 FClamp ±35 (CF_29~38 체인 복제)
# 삽입점: Ledge_LineSnap 내 selL/selR(게이트 후) → [K체인] → SetL/SetR 값핀 재배선
# 실행: py linesnap3_kx.py         (사전 점검)
#       py linesnap3_kx.py apply   (적용)
import json
import sys
import urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GF = "Ledge_LineSnap"
KML = "KismetMathLibrary"
K = "3.0"
CLAMP = ("-35.0", "35.0")
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"


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
    return {n["id"]: n for n in bq("get_graph_data", {"graph_name": GF})["nodes"]}


def pins(nodes: dict, nid: str) -> dict:
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


def pie_on() -> bool:
    r = call("editor_query", "run_python", {
        "command": "import unreal;print(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None)",
        "mode": "execute_file"})
    return "True" in json.dumps(r.get("output", []))


fn = graph()
# then-브랜치 Set(값핀 연결 있는 쪽)과 그 소스 sel 찾기
sets = {}
for nid, n in fn.items():
    if "VariableSet" not in n["class"]:
        continue
    pm = pins(fn, nid)
    for s, vp in (("L", "LedgeSnapDzL"), ("R", "LedgeSnapDzR")):
        if vp in pm and (pm[vp].get("connected_to") or []):
            sets[s] = (nid, vp, pm[vp]["connected_to"][0])
ok = True
sel = {}
for s in ("L", "R"):
    got = sets.get(s)
    good = got is not None
    if good:
        sel[s] = got[2].split(".")[0]
    print("[PF]", "OK " if good else "FAIL", f"Set{s} ← {got}")
    ok = ok and good
if not APPLY:
    print("[PF] 사전 점검", "통과 — apply로 실행" if ok else "실패")
    sys.exit(0 if ok else 1)
assert ok
assert not pie_on(), "PIE 실행 중 — 종료 후 재실행"

made = {}


def add(key: str, fname: str, pos: list) -> str:
    r = bq("add_node", {"graph_name": GF, "node_type": "CallFunction",
                        "function_class": KML, "function_name": fname, "position": pos})
    nid = r.get("id") or r.get("node_id")
    made[key] = nid
    return nid


def wire(sk: str, sp: str, tk: str, tp: str) -> None:
    bq("connect_pins", {"graph_name": GF,
                        "source_node": made.get(sk, sk), "source_pin": sp,
                        "target_node": made.get(tk, tk), "target_pin": tp})


def pindef(key: str, pin: str, value: str) -> None:
    bq("set_pin_default", {"graph_name": GF, "node_id": made[key], "pin_name": pin, "value": value})


X, Y = 1750, 400
add("sum", "Add_DoubleDouble", [X, Y])
add("mean", "Multiply_DoubleDouble", [X + 150, Y])
pindef("mean", "B", "0.5")
wire(sel["L"], "ReturnValue", "sum", "A")
wire(sel["R"], "ReturnValue", "sum", "B")
wire("sum", "ReturnValue", "mean", "A")
for i, s in enumerate(("L", "R")):
    yo = Y + 120 + i * 140
    add("dev" + s, "Subtract_DoubleDouble", [X + 300, yo])
    add("kx" + s, "Multiply_DoubleDouble", [X + 450, yo])
    add("out" + s, "Add_DoubleDouble", [X + 600, yo])
    add("cl" + s, "FClamp", [X + 750, yo])
    pindef("kx" + s, "B", K)
    pindef("cl" + s, "Min", CLAMP[0])
    pindef("cl" + s, "Max", CLAMP[1])
    wire(sel[s], "ReturnValue", "dev" + s, "A")
    wire("mean", "ReturnValue", "dev" + s, "B")
    wire("dev" + s, "ReturnValue", "kx" + s, "A")
    wire("mean", "ReturnValue", "out" + s, "A")
    wire("kx" + s, "ReturnValue", "out" + s, "B")
    wire("out" + s, "ReturnValue", "cl" + s, "Value")
    # Set 값핀 재배선
    set_nid, vp, _ = sets[s]
    bq("disconnect_pins", {"graph_name": GF, "source_node": sel[s], "source_pin": "ReturnValue",
                           "target_node": set_nid, "target_pin": vp})
    wire("cl" + s, "ReturnValue", set_nid, vp)
print("[K] 체인 배선 완료")

r = bq("compile_blueprint", {})
print("[COMPILE]", json.dumps(r)[:200])

fn2 = graph()
v = []
for s in ("L", "R"):
    set_nid, vp, _ = sets[s]
    v.append((pins(fn2, set_nid)[vp]["connected_to"] == [made["cl" + s] + ".ReturnValue"], f"Set{s} ← 클램프(K체인)"))
    v.append((pins(fn2, made["dev" + s])["A"]["connected_to"] == [sel[s] + ".ReturnValue"], f"dev{s} ← sel{s}"))
    v.append((pins(fn2, made["out" + s])["A"]["connected_to"] == [made["mean"] + ".ReturnValue"], f"out{s} ← mean"))
allok = True
for good, label in v:
    print("[CHK]", "OK " if good else "FAIL", label)
    allok = allok and good
assert allok, "링크 검증 실패"
print("[DONE] K=3 과장 적용 — PIE 실측 대기")
