# Phase 1 — DestFix 후보점 검증용 (2026-07-22)
# 목적: 손 타깃 Lerp B(라이브 외삽)를 래치 고정점으로 바꾸기 전, EndGrip 후보의 부호를 PIE로 확정.
#   - Ledge_HandTarget: LedgeUnitMoveVec = dir2D벡터 × (Td-Current) 를 재래치 에지(CF_220)에서 래치
#   - LedgeDebugs: AnchorL/R ± Vec 구체 4개 (+후보 반경7 / -후보 반경14)
# 저장 안 함 — PIE 확인 후 부호 확정되면 Phase 2에서 Lerp B 교체.
import json
import urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
KML = "KismetMathLibrary"
KSL = "KismetSystemLibrary"
HT = "Ledge_HandTarget"
DBG = "LedgeDebugs"
LOG = {"steps": [], "fails": []}


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:250])
    return json.loads(txt)


def graph(name):
    g = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": name})
    return {n["id"]: n for n in g["nodes"]}


def pin_src(nodes, nid, pin):
    for p in nodes[nid]["pins"]:
        if p["name"] == pin and p.get("direction") == "input":
            c = p.get("connected_to") or []
            return c[0] if c else None
    return None


def pin_dst(nodes, nid, pin):
    for p in nodes[nid]["pins"]:
        if p["name"] == pin and p.get("direction") == "output":
            return p.get("connected_to") or []
    return []


def harvest(o, tmap):
    if isinstance(o, dict):
        if o.get("temp_id") and (o.get("node_id") or o.get("id")):
            tmap[o["temp_id"]] = o.get("node_id") or o.get("id")
        else:
            for v in o.values():
                harvest(v, tmap)
    elif isinstance(o, list):
        for e in o:
            harvest(e, tmap)


# ── 1. 앵커 사전검증 (스테일 ID 방어) ──
ht = graph(HT)
checks = [
    ("K2Node_CallFunction_166", "A", "K2Node_CallFunction_193.ReturnValue"),   # dir2D벡터
    ("K2Node_CallFunction_209", "A", "K2Node_CallFunction_163.ReturnValue"),   # Td-Current
    ("K2Node_CallFunction_221", "bPickA", None),                                # 재래치 OR 경유 (knot 허용)
]
for nid, pin, want in checks:
    src = pin_src(ht, nid, pin)
    if want and src != want:
        raise SystemExit("앵커 불일치 %s.%s: %s (기대 %s)" % (nid, pin, src, want))
# 재래치 OR 소스 확인 (knot 통과)
relatch_src = "K2Node_CallFunction_220.ReturnValue"
if relatch_src.split(".")[0] not in ht:
    raise SystemExit("재래치 OR(CF_220) 없음")
# VS_26(Set AnchorR)의 then 타깃 기록
vs26_then = pin_dst(ht, "K2Node_VariableSet_26", "then")
if len(vs26_then) != 1:
    raise SystemExit("VS_26.then 예상 밖: %s" % vs26_then)
old_next = vs26_then[0]  # "노드ID.핀명"
LOG["steps"].append("anchors verified; VS_26.then -> " + old_next)

# ── 2. 변수 추가 ──
try:
    call("blueprint_query", "add_variable",
         {"asset_path": ABP, "name": "LedgeUnitMoveVec", "type": "struct:Vector", "category": "Ledge"})
    LOG["steps"].append("var LedgeUnitMoveVec added")
except RuntimeError as e:
    if "exist" in str(e).lower():
        LOG["steps"].append("var already exists — reuse")
    else:
        raise

# ── 3. Ledge_HandTarget: 래치 노드 4개 ──
specs = [
    {"temp_id": "g_vec", "node_type": "VariableGet", "variable_name": "LedgeUnitMoveVec", "position": [3600, 2600]},
    {"temp_id": "mult", "node_type": "CallFunction", "function_name": "Multiply_VectorFloat", "target_class": KML, "position": [3800, 2500]},
    {"temp_id": "sel", "node_type": "CallFunction", "function_name": "SelectVector", "target_class": KML, "position": [4000, 2550]},
    {"temp_id": "setv", "node_type": "VariableSet", "variable_name": "LedgeUnitMoveVec", "position": [4200, 2500]},
]
res = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": HT, "nodes": specs})
tm = {}
harvest(res, tm)
if len(tm) != 4:
    raise SystemExit("HT 노드 생성 실패: " + json.dumps(res)[:300])
LOG["steps"].append("HT nodes: %s" % tm)

conns = [
    {"source_node": "K2Node_CallFunction_193", "source_pin": "ReturnValue", "target_node": tm["mult"], "target_pin": "A"},
    {"source_node": "K2Node_CallFunction_163", "source_pin": "ReturnValue", "target_node": tm["mult"], "target_pin": "B"},
    {"source_node": tm["mult"], "source_pin": "ReturnValue", "target_node": tm["sel"], "target_pin": "A"},
    {"source_node": tm["g_vec"], "source_pin": "LedgeUnitMoveVec", "target_node": tm["sel"], "target_pin": "B"},
    {"source_node": "K2Node_CallFunction_220", "source_pin": "ReturnValue", "target_node": tm["sel"], "target_pin": "bPickA"},
    {"source_node": tm["sel"], "source_pin": "ReturnValue", "target_node": tm["setv"], "target_pin": "LedgeUnitMoveVec"},
]
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": HT, "connections": conns})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
LOG["fails"] += fails

# exec 스플라이스: VS_26.then → setv → (구 타깃)
old_nid, old_pin = old_next.split(".", 1)
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": HT,
                                            "node_id": "K2Node_VariableSet_26", "pin_name": "then"})
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": HT, "connections": [
    {"source_node": "K2Node_VariableSet_26", "source_pin": "then", "target_node": tm["setv"], "target_pin": "execute"},
    {"source_node": tm["setv"], "source_pin": "then", "target_node": old_nid, "target_pin": old_pin},
]})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
LOG["fails"] += fails
LOG["steps"].append("HT exec spliced")

# ── 4. LedgeDebugs: 구체 4개 ──
dbg = graph(DBG)
gate_then = pin_dst(dbg, "K2Node_IfThenElse_6", "then")
if len(gate_then) != 1:
    raise SystemExit("DBG 게이트 then 예상 밖: %s" % gate_then)
dbg_next = gate_then[0]
specs = [
    {"temp_id": "ga_l", "node_type": "VariableGet", "variable_name": "LedgeHandAnchorL", "position": [400, 2400]},
    {"temp_id": "ga_r", "node_type": "VariableGet", "variable_name": "LedgeHandAnchorR", "position": [400, 2500]},
    {"temp_id": "g_v", "node_type": "VariableGet", "variable_name": "LedgeUnitMoveVec", "position": [400, 2600]},
    {"temp_id": "add_l", "node_type": "CallFunction", "function_name": "Add_VectorVector", "target_class": KML, "position": [650, 2380]},
    {"temp_id": "add_r", "node_type": "CallFunction", "function_name": "Add_VectorVector", "target_class": KML, "position": [650, 2470]},
    {"temp_id": "sub_l", "node_type": "CallFunction", "function_name": "Subtract_VectorVector", "target_class": KML, "position": [650, 2560]},
    {"temp_id": "sub_r", "node_type": "CallFunction", "function_name": "Subtract_VectorVector", "target_class": KML, "position": [650, 2650]},
    {"temp_id": "s_pl", "node_type": "CallFunction", "function_name": "DrawDebugSphere", "target_class": KSL, "position": [950, 2380]},
    {"temp_id": "s_pr", "node_type": "CallFunction", "function_name": "DrawDebugSphere", "target_class": KSL, "position": [1200, 2380]},
    {"temp_id": "s_ml", "node_type": "CallFunction", "function_name": "DrawDebugSphere", "target_class": KSL, "position": [1450, 2380]},
    {"temp_id": "s_mr", "node_type": "CallFunction", "function_name": "DrawDebugSphere", "target_class": KSL, "position": [1700, 2380]},
]
res = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": DBG, "nodes": specs})
td = {}
harvest(res, td)
if len(td) != 11:
    raise SystemExit("DBG 노드 생성 실패(%d/11): %s" % (len(td), json.dumps(res)[:300]))
LOG["steps"].append("DBG nodes: %s" % td)

call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": ABP, "graph_name": DBG, "defaults": [
    {"node_id": td["s_pl"], "pin_name": "Radius", "value": "7.0"},
    {"node_id": td["s_pr"], "pin_name": "Radius", "value": "7.0"},
    {"node_id": td["s_ml"], "pin_name": "Radius", "value": "14.0"},
    {"node_id": td["s_mr"], "pin_name": "Radius", "value": "14.0"},
    {"node_id": td["s_pl"], "pin_name": "LineColor", "value": "(R=1.000000,G=1.000000,B=0.000000,A=1.000000)"},
    {"node_id": td["s_pr"], "pin_name": "LineColor", "value": "(R=1.000000,G=1.000000,B=0.000000,A=1.000000)"},
    {"node_id": td["s_ml"], "pin_name": "LineColor", "value": "(R=0.000000,G=1.000000,B=1.000000,A=1.000000)"},
    {"node_id": td["s_mr"], "pin_name": "LineColor", "value": "(R=0.000000,G=1.000000,B=1.000000,A=1.000000)"},
]})

conns = [
    {"source_node": td["ga_l"], "source_pin": "LedgeHandAnchorL", "target_node": td["add_l"], "target_pin": "A"},
    {"source_node": td["g_v"], "source_pin": "LedgeUnitMoveVec", "target_node": td["add_l"], "target_pin": "B"},
    {"source_node": td["ga_r"], "source_pin": "LedgeHandAnchorR", "target_node": td["add_r"], "target_pin": "A"},
    {"source_node": td["g_v"], "source_pin": "LedgeUnitMoveVec", "target_node": td["add_r"], "target_pin": "B"},
    {"source_node": td["ga_l"], "source_pin": "LedgeHandAnchorL", "target_node": td["sub_l"], "target_pin": "A"},
    {"source_node": td["g_v"], "source_pin": "LedgeUnitMoveVec", "target_node": td["sub_l"], "target_pin": "B"},
    {"source_node": td["ga_r"], "source_pin": "LedgeHandAnchorR", "target_node": td["sub_r"], "target_pin": "A"},
    {"source_node": td["g_v"], "source_pin": "LedgeUnitMoveVec", "target_node": td["sub_r"], "target_pin": "B"},
    {"source_node": td["add_l"], "source_pin": "ReturnValue", "target_node": td["s_pl"], "target_pin": "Center"},
    {"source_node": td["add_r"], "source_pin": "ReturnValue", "target_node": td["s_pr"], "target_pin": "Center"},
    {"source_node": td["sub_l"], "source_pin": "ReturnValue", "target_node": td["s_ml"], "target_pin": "Center"},
    {"source_node": td["sub_r"], "source_pin": "ReturnValue", "target_node": td["s_mr"], "target_pin": "Center"},
]
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": DBG, "connections": conns})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
LOG["fails"] += fails

# exec 스플라이스: 게이트.then → s_pl → s_pr → s_ml → s_mr → (구 타깃)
dn_nid, dn_pin = dbg_next.split(".", 1)
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": DBG,
                                            "node_id": "K2Node_IfThenElse_6", "pin_name": "then"})
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": DBG, "connections": [
    {"source_node": "K2Node_IfThenElse_6", "source_pin": "then", "target_node": td["s_pl"], "target_pin": "execute"},
    {"source_node": td["s_pl"], "source_pin": "then", "target_node": td["s_pr"], "target_pin": "execute"},
    {"source_node": td["s_pr"], "source_pin": "then", "target_node": td["s_ml"], "target_pin": "execute"},
    {"source_node": td["s_ml"], "source_pin": "then", "target_node": td["s_mr"], "target_pin": "execute"},
    {"source_node": td["s_mr"], "source_pin": "then", "target_node": dn_nid, "target_pin": dn_pin},
]})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
LOG["fails"] += fails
LOG["steps"].append("DBG exec spliced")

# ── 5. 컴파일 + 사후검증 ──
cp = call("blueprint_query", "compile", {"asset_path": ABP})
LOG["steps"].append("compile: %s" % json.dumps(cp)[:200])

ht2 = graph(HT)
ok1 = pin_src(ht2, tm["setv"], "LedgeUnitMoveVec") == tm["sel"] + ".ReturnValue"
ok2 = pin_src(ht2, tm["setv"], "execute") is not None
dbg2 = graph(DBG)
ok3 = pin_src(dbg2, td["s_pl"], "Center") == td["add_l"] + ".ReturnValue"
ok4 = pin_src(dbg2, td["s_mr"], "execute") is not None
LOG["steps"].append("post-verify: setv.val=%s setv.exec=%s sphere.center=%s sphere.exec=%s" % (ok1, ok2, ok3, ok4))

json.dump(LOG, open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/phase1_destfix.json", "w"), indent=1, ensure_ascii=False)
print("PHASE1_DONE fails=%d" % len(LOG["fails"]))
for s in LOG["steps"]:
    print("  " + s)
if LOG["fails"]:
    print("FAILS:", json.dumps(LOG["fails"], ensure_ascii=False)[:500])
