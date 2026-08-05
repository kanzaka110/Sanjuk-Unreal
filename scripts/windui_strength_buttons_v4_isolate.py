# 윈드 강도 UI 버튼 v4 — 기존 노드와 분리 (2026-08-05, 승호 지시 "기존 노드랑 섞지말고 별도로")
#   v3에서 섞인 2곳 해체:
#   ① InitWind.Comp <- 스텝퍼의 CallFunction_138 재사용 -> 전용 Literal(Actor8)+GetComponentByClass 신설
#   ② IfThenElse_10 Condition에 끼운 BooleanAND 게이트 -> 원상복구(CallFunction_141 직결) + AND/Get/변수 제거
#   진입점만 SEQ_1.then_4 (빈 핀) 유지 — BeginPlay 엔트리는 레벨BP에 하나뿐이라 공유 불가피
import json
import urllib.request
import atexit

URL = "http://localhost:9316/mcp"
MAP_BP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/SBWind_Weight_TEST01_Map"
EG = "EventGraph"
BR = "K2Node_IfThenElse_10"
COND_SRC = ("K2Node_CallFunction_141", "ReturnValue")  # 게이트 삽입 전 원래 Condition 소스
SEQ1 = "K2Node_ExecutionSequence_1"
ACTOR8 = ("/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/SBWind_Weight_TEST01_Map.SBWind_Weight_TEST01_Map"
          ":PersistentLevel.SBDirectionalWindActor_UAID_30560F6BCAE540F302_1731448399")
LOG = {"steps": [], "errors": []}
atexit.register(lambda: print(json.dumps(LOG, ensure_ascii=False, indent=1)))


def call(tool: str, action: str, params: dict, timeout: int = 300) -> dict:
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:500])
    return json.loads(txt)


def bpq(action: str, params: dict) -> dict:
    return call("blueprint_query", action, params)


def nid_of(r: dict) -> str:
    return r.get("node_id") or r.get("id")


def add(ntype: str, x: int, y: int, **kw) -> str:
    p = {"asset_path": MAP_BP, "graph_name": EG, "node_type": ntype, "position": [x, y]}
    p.update(kw)
    return nid_of(bpq("add_node", p))


def connect(cs: list) -> int:
    rc = bpq("connect_pins_bulk", {"asset_path": MAP_BP, "graph_name": EG, "connections": cs})
    fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    if fails:
        LOG["errors"].append({"conns": fails})
    return len(fails)


def graph_nodes() -> dict:
    g = bpq("get_graph_data", {"asset_path": MAP_BP, "graph_name": EG})
    return {n["id"]: n for n in g["nodes"]}


def pm(nodes: dict, nid: str) -> dict:
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


def node_pins(nid: str) -> dict:
    det = bpq("get_node_details", {"asset_path": MAP_BP, "graph_name": EG, "node_id": nid})
    return {p.get("name"): p for p in (det.get("pins") or [])}


def follow(nodes: dict, nid: str, pin: str) -> tuple:
    c = pm(nodes, nid)[pin].get("connected_to") or []
    assert c, "%s.%s 미연결" % (nid, pin)
    s = c[0]
    if isinstance(s, str):
        return tuple(s.rsplit(".", 1))
    return (s.get("node") or s.get("node_id"), s.get("pin") or s.get("pin_name"))


nodes = graph_nodes()
# v3 체인 노드 재특정 (exec 추적: then_4 -> crt -> cast -> init)
crt, _ = follow(nodes, SEQ1, "then_4")
cast, _ = follow(nodes, crt, "then")
init, _ = follow(nodes, cast, "then")
assert "Comp" in pm(nodes, init), "init 노드 특정 실패: %s" % init
# AND 게이트 특정 (BR.Condition <- AND.ReturnValue, AND.B <- VariableGet)
andn, and_pin = follow(nodes, BR, "Condition")
assert and_pin == "ReturnValue" and "A" in pm(nodes, andn) and "B" in pm(nodes, andn), \
    "AND 게이트 예상 불일치: %s.%s" % (andn, and_pin)
vg_step, _ = follow(nodes, andn, "B")
assert vg_step.startswith("K2Node_VariableGet"), "UseWindStepper Get 특정 실패: %s" % vg_step
LOG["steps"].append("특정: crt=%s cast=%s init=%s and=%s vg=%s" % (crt, cast, init, andn, vg_step))

# ═══ ① 게이트 원상복구 ═══
bpq("disconnect_pins", {"asset_path": MAP_BP, "graph_name": EG, "node_id": BR, "pin_name": "Condition"})
bpq("remove_node", {"asset_path": MAP_BP, "graph_name": EG, "node_id": andn})
bpq("remove_node", {"asset_path": MAP_BP, "graph_name": EG, "node_id": vg_step})
f = connect([{"source_node": COND_SRC[0], "source_pin": COND_SRC[1], "target_node": BR, "target_pin": "Condition"}])
assert f == 0, "Condition 원복 배선 실패"
LOG["steps"].append("게이트 해체 + Condition 원복 OK")
for act in ("remove_variable", "delete_variable"):
    try:
        bpq(act, {"asset_path": MAP_BP, "name": "UseWindStepper", "variable_name": "UseWindStepper"})
        LOG["steps"].append("UseWindStepper 변수 제거 (%s)" % act)
        break
    except Exception as e:
        LOG["steps"].append("%s 실패(무해): %s" % (act, str(e)[:120]))

# ═══ ② 전용 Actor8 참조 체인 ═══
bpq("disconnect_pins", {"asset_path": MAP_BP, "graph_name": EG, "node_id": init, "pin_name": "Comp"})
lit = add("K2Node_Literal", -1250, 2650)
bpq("set_node_property", {"asset_path": MAP_BP, "graph_name": EG, "node_id": lit,
                          "property_name": "ObjectRef", "value": ACTOR8})
bpq("refresh_node", {"asset_path": MAP_BP, "graph_name": EG, "node_id": lit})
lit_pins = node_pins(lit)
out_pin = next((p for p in lit_pins if lit_pins[p].get("direction") != "input" and p not in ("execute", "then")), None)
assert out_pin, "리터럴 출력핀 미생성: %s" % list(lit_pins)
LOG["steps"].append("Literal OK (출력핀=%s, 타입=%s)" % (out_pin, lit_pins[out_pin].get("type")))

gcbc = add("CallFunction", -950, 2650, function_name="GetComponentByClass", target_class="Actor")
bpq("set_pin_default", {"asset_path": MAP_BP, "graph_name": EG, "node_id": gcbc,
                        "pin_name": "ComponentClass", "value": "/Script/SB2.SBDirectionalWindComponent"})
f = connect([
    {"source_node": lit, "source_pin": out_pin, "target_node": gcbc, "target_pin": "self"},
    {"source_node": gcbc, "source_pin": "ReturnValue", "target_node": init, "target_pin": "Comp"},
])
assert f == 0, "전용 참조 체인 배선 실패"
LOG["steps"].append("전용 Literal+GetComponentByClass -> InitWind.Comp OK")

cr = bpq("compile_blueprint", {"asset_path": MAP_BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:300])
assert not cr.get("errors"), "컴파일 에러: %s" % cr

# ═══ ③ 검증 ═══
nodes2 = graph_nodes()
gp = pm(nodes2, gcbc)
checks = {
    "BR.Condition<-141": follow(nodes2, BR, "Condition")[0] == COND_SRC[0],
    "init.Comp<-gcbc": follow(nodes2, init, "Comp")[0] == gcbc,
    "gcbc.self<-lit": follow(nodes2, gcbc, "self")[0] == lit,
    "gcbc.ret_type": gp["ReturnValue"].get("type"),
    "gcbc.class": gp["ComponentClass"].get("default_object") or gp["ComponentClass"].get("default_value"),
    "and_removed": andn not in nodes2 and vg_step not in nodes2,
}
LOG["steps"].append({"verify": checks})
assert checks["BR.Condition<-141"] and checks["init.Comp<-gcbc"] and checks["and_removed"], "검증 실패"
LOG["steps"].append("v4 완료 — 버튼 체인 완전 독립 (공유는 SEQ_1.then_4 진입핀뿐). 맵 미저장")
