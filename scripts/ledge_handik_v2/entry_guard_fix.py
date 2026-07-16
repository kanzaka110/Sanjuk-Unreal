# v13b — entry_guard 보정 2종
# ① 가드에 prev-이동 게이트 추가: (bPrevTransitMoving OR bPrevTransitingToNextLedge)
#    → 이동 종료 에지 프레임에서만 홀드. 점프→렛지 진입(이동이력 없음)은 즉시 픽.
#    bPrevTransitingToNextLedge 신설 + UpdateStates VS_19.then→[Set prevTr]→VS_20 스플라이스.
# ② IsStateMachineBlendStackAnimInBlendOut: LessEqual.B(0.5 상수) ← SelectFloat(bActive ? LedgeBlendOutTime : 0.5)
#    렛지 한정 블렌드아웃 문턱 0.15 (LedgeBlendOutTime 변수, 튜닝 가능). 지상 영향 없음.
# 롤백: ① and4→Condition 원복 + or1/and5/게터 삭제, VS_19.then→VS_20 원복 ② LessEqual.B 연결 해제(디폴트 0.5 복원)
# ⚠ 로컬 python 전용 — 에디터 콘솔(py) 실행 금지.
import json, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
KML = "KismetMathLibrary"
LOG = {"steps": [], "errors": []}


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


def harvest(o, tm):
    if isinstance(o, dict):
        if o.get("temp_id") and (o.get("node_id") or o.get("id")):
            tm[o["temp_id"]] = o.get("node_id") or o.get("id")
        else:
            for v in o.values():
                harvest(v, tm)
    elif isinstance(o, list):
        for e in o:
            harvest(e, tm)


def graph(gname):
    g = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": gname})
    return {n["id"]: n for n in g["nodes"]}


def pins(n):
    return {p["name"]: p for p in n.get("pins", [])}


def conn(n, pin):
    return (pins(n).get(pin, {}).get("connected_to") or [])


# ── 변수 ──
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": ABP}).get("variables", [])}
for name, typ, dv in (("bPrevTransitingToNextLedge", "bool", None), ("LedgeBlendOutTime", "float", "0.15")):
    if name in existing:
        continue
    p = {"asset_path": ABP, "name": name, "type": typ, "category": "Ledge|TransitHold", "instance_editable": False}
    if dv:
        p["default_value"] = dv
    call("blueprint_query", "add_variable", p)
    LOG["steps"].append("var: " + name)

# ══ ① UpdateStates: prevTr 스플라이스 ══
G1 = "UpdateStates"
nodes = graph(G1)
# 앵커를 타이틀로 재확인 (ID 세션 불안정 대비)
VS19 = VS20 = None
for nid, n in nodes.items():
    t = n.get("title", "")
    if n["class"] == "K2Node_VariableSet":
        if "bTransitMoving" in t and "Prev" not in t:
            VS19 = nid
        elif "TransitingToNextLedge" in t and "Prev" not in t:
            VS20 = nid
if not (VS19 and VS20):
    raise SystemExit("UpdateStates 앵커 소실 VS19=%s VS20=%s" % (VS19, VS20))
if VS20 not in str(conn(nodes[VS19], "then")):
    raise SystemExit("VS19.then->%s (예상: VS20)" % conn(nodes[VS19], "then"))
spec1 = [
    {"temp_id": "gTrOld", "node_type": "VariableGet", "variable_name": "TransitingToNextLedge", "position": [1560, 60]},
    {"temp_id": "setPrevTr", "node_type": "VariableSet", "variable_name": "bPrevTransitingToNextLedge", "position": [1560, -60]},
]
tm1 = {}
harvest(call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": G1, "nodes": spec1}), tm1)
if len(tm1) != 2:
    raise SystemExit("① 노드 생성 실패: " + str(tm1))
n_new = graph(G1)
if not n_new[tm1["gTrOld"]].get("pins") or not n_new[tm1["setPrevTr"]].get("pins"):
    raise SystemExit("① 빈 노드")
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": G1, "node_id": VS19, "pin_name": "then"})
rc1 = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": G1, "connections": [
    {"source_node": tm1["gTrOld"], "source_pin": "TransitingToNextLedge", "target_node": tm1["setPrevTr"], "target_pin": "bPrevTransitingToNextLedge"},
    {"source_node": VS19, "source_pin": "then", "target_node": tm1["setPrevTr"], "target_pin": "execute"},
    {"source_node": tm1["setPrevTr"], "source_pin": "then", "target_node": VS20, "target_pin": "execute"},
]})
f1 = [x for x in (rc1.get("results") or []) if not x.get("success", True)]
if f1:
    LOG["errors"].append(("①", f1))
LOG["steps"].append("① UpdateStates splice OK" if not f1 else "① FAIL")

# ══ ② 가드 조건 확장: and5 = and4 AND (prevMv OR prevTr) ══
G2 = "OnStateEntry_EventTransit"
nodes = graph(G2)
brA = and4 = None
for nid, n in nodes.items():
    if n["class"] == "K2Node_IfThenElse":
        brA = nid
if not brA:
    raise SystemExit("② Branch 소실")
cond_src = conn(nodes[brA], "Condition")
if not cond_src:
    raise SystemExit("② Condition 미연결")
and4 = cond_src[0].split(".")[0]
spec2 = [
    {"temp_id": "gPrevMv", "node_type": "VariableGet", "variable_name": "bPrevTransitMoving", "position": [-980, 1060]},
    {"temp_id": "gPrevTr", "node_type": "VariableGet", "variable_name": "bPrevTransitingToNextLedge", "position": [-980, 1140]},
    {"temp_id": "orPrev", "node_type": "CallFunction", "function_name": "BooleanOR", "target_class": KML, "position": [-700, 1100]},
    {"temp_id": "and5", "node_type": "CallFunction", "function_name": "BooleanAND", "target_class": KML, "position": [140, 900]},
]
tm2 = {}
harvest(call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": G2, "nodes": spec2}), tm2)
if len(tm2) != 4:
    raise SystemExit("② 노드 생성 실패: " + str(tm2))
n_new = graph(G2)
for tid in tm2:
    if not n_new[tm2[tid]].get("pins"):
        raise SystemExit("② 빈 노드: " + tid)
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": G2, "node_id": brA, "pin_name": "Condition"})
rc2 = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": G2, "connections": [
    {"source_node": tm2["gPrevMv"], "source_pin": "bPrevTransitMoving", "target_node": tm2["orPrev"], "target_pin": "A"},
    {"source_node": tm2["gPrevTr"], "source_pin": "bPrevTransitingToNextLedge", "target_node": tm2["orPrev"], "target_pin": "B"},
    {"source_node": and4, "source_pin": "ReturnValue", "target_node": tm2["and5"], "target_pin": "A"},
    {"source_node": tm2["orPrev"], "source_pin": "ReturnValue", "target_node": tm2["and5"], "target_pin": "B"},
    {"source_node": tm2["and5"], "source_pin": "ReturnValue", "target_node": brA, "target_pin": "Condition"},
]})
f2 = [x for x in (rc2.get("results") or []) if not x.get("success", True)]
if f2:
    LOG["errors"].append(("②", f2))
LOG["steps"].append("② guard prev-gate OK" if not f2 else "② FAIL")

# ══ ③ IsStateMachineBlendStackAnimInBlendOut: 문턱 Select ══
G3 = "IsStateMachineBlendStackAnimInBlendOut"
nodes = graph(G3)
LE = None
for nid, n in nodes.items():
    if n["class"] == "K2Node_PromotableOperator" and n.get("function") == "LessEqual_DoubleDouble":
        LE = nid
if not LE:
    raise SystemExit("③ LessEqual 소실")
if conn(nodes[LE], "B"):
    raise SystemExit("③ LessEqual.B 이미 연결됨: " + str(conn(nodes[LE], "B")))
spec3 = [
    {"temp_id": "gLMD", "node_type": "VariableGet", "variable_name": "LedgeMoveData", "position": [656, 400]},
    {"temp_id": "brkLMD", "node_type": "BreakStruct", "struct_type": "SBLedgeMoveData", "position": [860, 400]},
    {"temp_id": "gBOT", "node_type": "VariableGet", "variable_name": "LedgeBlendOutTime", "position": [656, 320]},
    {"temp_id": "selF", "node_type": "CallFunction", "function_name": "SelectFloat", "target_class": KML, "position": [1040, 320]},
]
tm3 = {}
harvest(call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": G3, "nodes": spec3}), tm3)
if len(tm3) != 4:
    raise SystemExit("③ 노드 생성 실패: " + str(tm3))
n_new = graph(G3)
brk_in = bact = None
for p in n_new[tm3["brkLMD"]].get("pins", []):
    if p["direction"] == "input" and p["name"].startswith("SBLedgeMoveData"):
        brk_in = p["name"]
    if p["direction"] == "output" and p["name"] == "bActive":
        bact = p["name"]
sel_pins = [p["name"] for p in n_new[tm3["selF"]].get("pins", [])]
if not (brk_in and bact):
    raise SystemExit("③ Break 핀: " + str([p["name"] for p in n_new[tm3["brkLMD"]].get("pins", [])]))
if "bPickA" not in sel_pins:
    raise SystemExit("③ SelectFloat 핀: " + str(sel_pins))
call("blueprint_query", "set_pin_default", {"asset_path": ABP, "graph_name": G3, "node_id": tm3["selF"], "pin_name": "B", "value": "0.5"})
rc3 = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": G3, "connections": [
    {"source_node": tm3["gLMD"], "source_pin": "LedgeMoveData", "target_node": tm3["brkLMD"], "target_pin": brk_in},
    {"source_node": tm3["gBOT"], "source_pin": "LedgeBlendOutTime", "target_node": tm3["selF"], "target_pin": "A"},
    {"source_node": tm3["brkLMD"], "source_pin": bact, "target_node": tm3["selF"], "target_pin": "bPickA"},
    {"source_node": tm3["selF"], "source_pin": "ReturnValue", "target_node": LE, "target_pin": "B"},
]})
f3 = [x for x in (rc3.get("results") or []) if not x.get("success", True)]
if f3:
    LOG["errors"].append(("③", f3))
LOG["steps"].append("③ blendout select OK" if not f3 else "③ FAIL")

with open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/entry_guard_fix.json", "w") as fp:
    json.dump(LOG, fp, indent=1, ensure_ascii=False)
print("ENTRY_GUARD_FIX_DONE errors=%s" % ("none" if not LOG["errors"] else json.dumps(LOG["errors"], ensure_ascii=False)[:500]))
