# 경사 Z보정 M4 — DzBody 신호를 이동 커버 버전으로 교체 (2026-07-24)
# 구: mean(게이트된 DzL,DzR) — 정지 전용.  신: mean(실제 손타깃Z − 몸기준Z) → 이동 중 슬라이드 선행 포착
#   raw = 0.5*((HandWorldL.Z − WorldNowL.Z) + (HandWorldR.Z − WorldNowR.Z))
#   → FClamp ±35 → SelectFloat(bPickA=LedgeTransitActive ? 0 : raw) → FInterpTo(prev, 8) → Set LedgeSlopeDzBody
# 정지 시 HandWorld = WorldNow+Dz 이므로 자동으로 mean(DzL,DzR)과 일치 (기존 의미 포함)
# 실행: py slope_z_m4_body.py apply   (PIE off, Ledge_HandTarget 탭 닫기)
import json, sys, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GH = "Ledge_HandTarget"
KML = "KismetMathLibrary"
BK = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/H---------Claude-Sanjuk-Unreal/ef13a25b-b3a2-4f38-8323-b9b645ac51ec/scratchpad/slopeZ_m4_backup.json"
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"

M = {
    "bkWL": "K2Node_CallFunction_140", "bkWR": "K2Node_CallFunction_179",
    "addB": "K2Node_CallFunction_182", "mulB": "K2Node_CallFunction_183",
    "setB": "K2Node_VariableSet_19",
    "dtGet": "K2Node_VariableGet_9",
}


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
got = pins(nodes, M["setB"])["LedgeSlopeDzBody"]["connected_to"]
assert got == [M["mulB"] + ".ReturnValue"], "setB 전제 불일치: " + json.dumps(got)
assert "Delta Time" in pins(nodes, M["dtGet"]), "dtGet 핀 확인 실패"
print("[PF] 전제 OK")

if not APPLY:
    print("== dry-run 종료 ==")
    sys.exit(0)

assert not pie_on(), "PIE 실행 중 — 종료 후 apply"

exp = bq("get_graph_data", {"graph_name": GH})
with open(BK, "w", encoding="utf-8") as f:
    json.dump(exp, f)
print("[BK]", BK)

X, Y = 6600, -1750
made = {}


def add(key, ntype, extra, pos):
    p = {"graph_name": GH, "node_type": ntype, "position": pos}
    p.update(extra)
    r = bq("add_node", p)
    nid = r.get("id") or r.get("node_id")
    made[key] = nid
    print("[ADD]", key, "->", nid)
    return nid


add("getHWL", "VariableGet", {"variable_name": "LedgeHandWorldL"}, [X, Y])
add("getHWR", "VariableGet", {"variable_name": "LedgeHandWorldR"}, [X, Y + 120])
add("bkHL", "CallFunction", {"function_class": KML, "function_name": "BreakVector"}, [X + 180, Y])
add("bkHR", "CallFunction", {"function_class": KML, "function_name": "BreakVector"}, [X + 180, Y + 120])
add("subBL", "CallFunction", {"function_class": KML, "function_name": "Subtract_DoubleDouble"}, [X + 380, Y])
add("subBR", "CallFunction", {"function_class": KML, "function_name": "Subtract_DoubleDouble"}, [X + 380, Y + 120])
add("addB2", "CallFunction", {"function_class": KML, "function_name": "Add_DoubleDouble"}, [X + 560, Y + 60])
add("mulB2", "CallFunction", {"function_class": KML, "function_name": "Multiply_DoubleDouble"}, [X + 720, Y + 60])
add("clB", "CallFunction", {"function_class": KML, "function_name": "FClamp"}, [X + 880, Y + 60])
add("getTA", "VariableGet", {"variable_name": "LedgeTransitActive"}, [X + 880, Y + 190])
add("selB", "CallFunction", {"function_class": KML, "function_name": "SelectFloat"}, [X + 1060, Y + 60])
add("getPrev", "VariableGet", {"variable_name": "LedgeSlopeDzBody"}, [X + 1060, Y - 90])
add("fint", "CallFunction", {"function_class": KML, "function_name": "FInterpTo"}, [X + 1260, Y + 20])


def pindef(key, pin, value):
    bq("set_pin_default", {"graph_name": GH, "node_id": made[key], "pin_name": pin, "value": value})
    print("[DEF]", key, pin, "=", value)


pindef("mulB2", "B", "0.5")
pindef("clB", "Min", "-35.0")
pindef("clB", "Max", "35.0")
pindef("selB", "A", "0.0")
pindef("fint", "InterpSpeed", "8.0")


def wire(sk, sp, tk, tp):
    src = made.get(sk, M.get(sk, sk))
    tgt = made.get(tk, M.get(tk, tk))
    bq("connect_pins", {"graph_name": GH, "source_node": src, "source_pin": sp,
                        "target_node": tgt, "target_pin": tp})
    print("[WIRE]", sk + "." + sp, "->", tk + "." + tp)


wire("getHWL", "LedgeHandWorldL", "bkHL", "InVec")
wire("getHWR", "LedgeHandWorldR", "bkHR", "InVec")
wire("bkHL", "Z", "subBL", "A")
wire("bkWL", "Z", "subBL", "B")
wire("bkHR", "Z", "subBR", "A")
wire("bkWR", "Z", "subBR", "B")
wire("subBL", "ReturnValue", "addB2", "A")
wire("subBR", "ReturnValue", "addB2", "B")
wire("addB2", "ReturnValue", "mulB2", "A")
wire("mulB2", "ReturnValue", "clB", "Value")
wire("clB", "ReturnValue", "selB", "B")
wire("getTA", "LedgeTransitActive", "selB", "bPickA")
wire("getPrev", "LedgeSlopeDzBody", "fint", "Current")
wire("selB", "ReturnValue", "fint", "Target")
wire("dtGet", "Delta Time", "fint", "DeltaTime")
bq("disconnect_pins", {"graph_name": GH, "source_node": M["mulB"], "source_pin": "ReturnValue",
                       "target_node": M["setB"], "target_pin": "LedgeSlopeDzBody"})
print("[CUT] mulB -X-> setB")
wire("fint", "ReturnValue", "setB", "LedgeSlopeDzBody")

# 구 addB/mulB 죽은 체인 정리 (개별 재조회)
for key in ("mulB", "addB"):
    cur = graph(GH)
    nid = M[key]
    if nid in cur:
        outs = [c for p in cur[nid].get("pins", []) if p["direction"] == "output" for c in p.get("connected_to", [])]
        if not outs:
            bq("remove_node", {"graph_name": GH, "node_id": nid})
            print("[DEL]", key, nid)
        else:
            print("[SKIP-DEL]", key, "잔여 소비자:", outs)

# ══ 검증 ══
nodes2 = graph(GH)
ok = True
chk = [
    (made["fint"] + ".ReturnValue", M["setB"], "LedgeSlopeDzBody"),
    (made["selB"] + ".ReturnValue", made["fint"], "Target"),
    (made["clB"] + ".ReturnValue", made["selB"], "B"),
    (M["bkWL"] + ".Z", made["subBL"], "B"),
    (M["bkWR"] + ".Z", made["subBR"], "B"),
]
for src, tn, tp in chk:
    got = pins(nodes2, tn).get(tp, {}).get("connected_to", [])
    good = got == [src]
    ok = ok and good
    print("[CHK]", "OK " if good else "FAIL", tn + "." + tp, "<-", got)
assert ok, "링크 검증 실패"

r = bq("compile_blueprint", {})
print("[COMPILE]", json.dumps(r)[:300])
