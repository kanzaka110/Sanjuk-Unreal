# 경사 Z보정 M2 — 폭주 방어 게이트 (2026-07-24)
# 증상: 스테일 스플라인 끝점 클램핑 → Dz -156 폭주 → 손 다이빙 (실측: 최근접점 XY 67cm 이탈)
# 수정: ①XY 거리 게이트 (Vector_Distance2D > 30cm → Dz 0)  ②FClamp ±35
#   subX → clampX → selX(bPickA=distXY<=30) → SetX/addB  (기존 subX→Set/addB 링크 대체)
# 실행: py slope_z_m2_guard.py apply   (PIE off, Ledge_HandTarget 탭 닫기)
import json, sys, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GH = "Ledge_HandTarget"
KML = "KismetMathLibrary"
DIST_GATE = "30.0"
CLAMP = "35.0"
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"

M = {
    "fcl": "K2Node_CallFunction_42", "fcr": "K2Node_CallFunction_157",
    "subL": "K2Node_CallFunction_142", "subR": "K2Node_CallFunction_181",
    "addB": "K2Node_CallFunction_182",
    "setL": "K2Node_VariableSet_15", "setR": "K2Node_VariableSet_16",
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
# 현재 링크 전제 확인
assert any(c == M["subL"] + ".ReturnValue" for c in pins(nodes, M["setL"])["LedgeSlopeDzL"]["connected_to"]), "subL->setL 전제 불일치"
assert any(c == M["subR"] + ".ReturnValue" for c in pins(nodes, M["setR"])["LedgeSlopeDzR"]["connected_to"]), "subR->setR 전제 불일치"
print("[PF] 전제 링크 OK")

if not APPLY:
    print("== dry-run 종료 ==")
    sys.exit(0)

assert not pie_on(), "PIE 실행 중 — 종료 후 apply"

X, Y = 5900, -1750
made = {}


def add(key, extra, pos):
    p = {"graph_name": GH, "node_type": "CallFunction", "position": pos}
    p.update(extra)
    r = bq("add_node", p)
    nid = r.get("id") or r.get("node_id")
    made[key] = nid
    print("[ADD]", key, "->", nid)
    return nid


for side, yoff in (("L", 0), ("R", 350)):
    add("d2" + side, {"function_class": KML, "function_name": "Vector_Distance2D"}, [X, Y + yoff])
    add("le" + side, {"function_class": KML, "function_name": "LessEqual_DoubleDouble"}, [X + 200, Y + yoff])
    add("cl" + side, {"function_class": KML, "function_name": "FClamp"}, [X, Y + 130 + yoff])
    add("sel" + side, {"function_class": KML, "function_name": "SelectFloat"}, [X + 420, Y + 60 + yoff])


def pindef(key, pin, value):
    bq("set_pin_default", {"graph_name": GH, "node_id": made[key], "pin_name": pin, "value": value})
    print("[DEF]", key, pin, "=", value)


for side in ("L", "R"):
    pindef("le" + side, "B", DIST_GATE)
    pindef("cl" + side, "Min", "-" + CLAMP)
    pindef("cl" + side, "Max", CLAMP)
    pindef("sel" + side, "B", "0.0")


def wire(sk, sp, tk, tp):
    src = made.get(sk, M.get(sk, sk))
    tgt = made.get(tk, M.get(tk, tk))
    bq("connect_pins", {"graph_name": GH, "source_node": src, "source_pin": sp,
                        "target_node": tgt, "target_pin": tp})
    print("[WIRE]", sk + "." + sp, "->", tk + "." + tp)


def cut(sk, sp, tk, tp):
    bq("disconnect_pins", {"graph_name": GH, "source_node": made.get(sk, M.get(sk, sk)), "source_pin": sp,
                           "target_node": made.get(tk, M.get(tk, tk)), "target_pin": tp})
    print("[CUT]", sk + "." + sp, "-X->", tk + "." + tp)


for side, WN, setvar in (("L", WNL, "LedgeSlopeDzL"), ("R", WNR, "LedgeSlopeDzR")):
    fc, sub, st = "fc" + side.lower(), "sub" + side, "set" + side
    # 거리 게이트
    wire(fc, "ReturnValue", "d2" + side, "V1")
    wire(WN, "ReturnValue", "d2" + side, "V2")
    wire("d2" + side, "ReturnValue", "le" + side, "A")
    # 클램프 + 선택
    wire(sub, "ReturnValue", "cl" + side, "Value")
    wire("cl" + side, "ReturnValue", "sel" + side, "A")
    wire("le" + side, "ReturnValue", "sel" + side, "bPickA")
    # 소비 대체
    cut(sub, "ReturnValue", st, setvar)
    wire("sel" + side, "ReturnValue", st, setvar)
    cut(sub, "ReturnValue", "addB", "A" if side == "L" else "B")
    wire("sel" + side, "ReturnValue", "addB", "A" if side == "L" else "B")

# ══ 검증 ══
nodes2 = graph(GH)


def srcs(nid, pin):
    return pins(nodes2, made.get(nid, M.get(nid, nid))).get(pin, {}).get("connected_to", [])


ok = True
for side, setvar in (("L", "LedgeSlopeDzL"), ("R", "LedgeSlopeDzR")):
    exp_set = [made["sel" + side] + ".ReturnValue"]
    got = srcs("set" + side, setvar)
    good = got == exp_set
    ok = ok and good
    print("[CHK]", "OK " if good else "FAIL", "set" + side, "<-", got)
gotA, gotB = srcs("addB", "A"), srcs("addB", "B")
goodB = gotA == [made["selL"] + ".ReturnValue"] and gotB == [made["selR"] + ".ReturnValue"]
ok = ok and goodB
print("[CHK]", "OK " if goodB else "FAIL", "addB A/B <-", gotA, gotB)
for side in ("L", "R"):
    good = bool(srcs("sel" + side, "bPickA")) and bool(srcs("cl" + side, "Value"))
    ok = ok and good
    print("[CHK]", "OK " if good else "FAIL", "sel" + side + " 게이트 배선")
assert ok, "링크 검증 실패"

r = bq("compile_blueprint", {})
print("[COMPILE]", json.dumps(r)[:300])
