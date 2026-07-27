# 경사 Z보정 M3 — 게이트 2D→3D 교체 (2026-07-24)
# 증상: 스테일 스플라인이 XY 22~27cm(게이트30 통과)·Z -87cm → 클램프 -35까지 끌려 팔 접힘
# 실측 분리도: 정상 3D ≤~15cm vs 스테일 67/92cm → Vector_Distance(3D) 45cm 게이트로 교체
# 실행: py slope_z_m3_gate3d.py apply   (PIE off, Ledge_HandTarget 탭 닫기)
import json, sys, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GH = "Ledge_HandTarget"
KML = "KismetMathLibrary"
GATE3D = "45.0"
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"

M = {
    "fcl": "K2Node_CallFunction_42", "fcr": "K2Node_CallFunction_157",
    "d2L": "K2Node_CallFunction_191", "d2R": "K2Node_CallFunction_202",
    "leL": "K2Node_CallFunction_194", "leR": "K2Node_CallFunction_216",
}
WNL, WNR = "K2Node_CallFunction_55", "K2Node_CallFunction_91"


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


def graph(g):
    return {n["id"]: n for n in bq("get_graph_data", {"graph_name": g})["nodes"]}


def pins(nodes, nid):
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


nodes = graph(GH)
missing = [k for k, v in M.items() if v not in nodes]
assert not missing, "노드 미발견: " + json.dumps(missing)
for side in ("L", "R"):
    got = pins(nodes, M["le" + side])["A"]["connected_to"]
    assert got == [M["d2" + side] + ".ReturnValue"], "le" + side + ".A 전제 불일치: " + json.dumps(got)
print("[PF] 전제 링크 OK")

if not APPLY:
    print("== dry-run 종료 ==")
    sys.exit(0)

assert not pie_on(), "PIE 실행 중 — 종료 후 apply"

made = {}
X, Y = 5900, -1550
for side, yoff in (("L", 0), ("R", 350)):
    r = bq("add_node", {"graph_name": GH, "node_type": "CallFunction", "position": [X, Y + yoff],
                        "function_class": KML, "function_name": "Vector_Distance"})
    nid = r.get("id") or r.get("node_id")
    made["nd" + side] = nid
    print("[ADD] nd" + side, "->", nid)


def wire(sk, sp, tk, tp):
    src = made.get(sk, M.get(sk, sk))
    tgt = made.get(tk, M.get(tk, tk))
    bq("connect_pins", {"graph_name": GH, "source_node": src, "source_pin": sp,
                        "target_node": tgt, "target_pin": tp})
    print("[WIRE]", sk + "." + sp, "->", tk + "." + tp)


for side, WN in (("L", WNL), ("R", WNR)):
    fc, nd, le, d2 = "fc" + side.lower(), "nd" + side, "le" + side, "d2" + side
    wire(fc, "ReturnValue", nd, "V1")
    wire(WN, "ReturnValue", nd, "V2")
    bq("disconnect_pins", {"graph_name": GH, "source_node": M[d2], "source_pin": "ReturnValue",
                           "target_node": M[le], "target_pin": "A"})
    print("[CUT]", d2, "-X->", le + ".A")
    wire(nd, "ReturnValue", le, "A")
    bq("set_pin_default", {"graph_name": GH, "node_id": M[le], "pin_name": "B", "value": GATE3D})
    print("[DEF]", le, "B =", GATE3D)

# 죽은 2D 노드 제거 (개별 재조회 후 — pitfalls)
for side in ("L", "R"):
    d2 = M["d2" + side]
    cur = graph(GH)
    if d2 in cur:
        outs = [c for p in cur[d2].get("pins", []) if p["direction"] == "output" for c in p.get("connected_to", [])]
        if not outs:
            bq("remove_node", {"graph_name": GH, "node_id": d2})
            print("[DEL]", d2)
        else:
            print("[SKIP-DEL]", d2, "잔여 소비자:", outs)

# ══ 검증 ══
nodes2 = graph(GH)
ok = True
for side in ("L", "R"):
    got = pins(nodes2, M["le" + side])["A"]["connected_to"]
    good = got == [made["nd" + side] + ".ReturnValue"]
    ok = ok and good
    print("[CHK]", "OK " if good else "FAIL", "le" + side + ".A <-", got)
    gotB = pins(nodes2, M["le" + side])["B"].get("default_value")
    print("[CHK]", "le" + side + ".B =", gotB)
assert ok, "링크 검증 실패"

r = bq("compile_blueprint", {})
print("[COMPILE]", json.dumps(r)[:300])
