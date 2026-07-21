# AM_SBLedgeIK 분류 재설계 + Idle 커브 벽 분기 (2026-07-21, 유저 지시)
#
# 지시:
#   - ToLadder_Far_*  : 이탈이 아니라 WallToWall 패턴(=이동)으로 처리
#   - LedgeSeeking_*  : IK 1 올타임 유지 (=정지)
#   - Idle/MoveToIdle : 이미 정지 (이름에 'Idle' 포함) — 변경 없음
#   - _Wallless 이면 손만 IK=1, 발은 끔
#
# 변경 1 (EventGraph 재배선):
#   현재  이탈 = OR(OR(ToLadder, End), BackwardJump) / 정지 = Idle
#   변경  이탈 = OR(End, BackwardJump)               / 정지 = OR(Idle, LedgeSeeking)
#   → CF_128 의 Substring 을 'ToLadder' -> 'LedgeSeeking' 으로 바꾸고 정지 쪽으로 이설.
#     ToLadder 는 어느 분기에도 안 걸리므로 자동으로 '이동'이 된다.
#
# 변경 2 (WriteIdleCurves):
#   발 커브(ledge_foot_ik_l/r) 의 Value 를 상수 1.0 -> SelectFloat(0.0 / 1.0, bPickA=Contains(name,'Wallless'))
#   손 커브는 항상 1.0 유지.
#
# 백업: am_ledgeik_BACKUP.json (EventGraph + WriteIdleCurves 원본)
import json, urllib.request

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/TA/AnimModifiers/AM_SBLedgeIK"
KML = "KismetMathLibrary"
LOG = {"steps": [], "fails": []}


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:300])
    return json.loads(txt)


# ── 사전 검증: 앵커가 예상과 같은지 (노드 ID 재할당 방어) ──
ev = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": "EventGraph"})
nodes = {n["id"]: n for n in ev["nodes"]}


def sub_of(nid):
    for p in nodes[nid]["pins"]:
        if p["name"] == "Substring":
            return p.get("default_value")
    return None


expect = {"K2Node_CallFunction_128": "ToLadder", "K2Node_CallFunction_129": "End",
          "K2Node_CallFunction_130": "BackwardJump", "K2Node_CallFunction_131": "Idle"}
for nid, want in expect.items():
    if nid not in nodes or sub_of(nid) != want:
        raise SystemExit("앵커 불일치: %s = %s (기대 %s)" % (nid, sub_of(nid), want))
LOG["steps"].append("anchors verified")

# ── 변경 1: 분류 재배선 ──
call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": BP, "graph_name": "EventGraph",
     "defaults": [{"node_id": "K2Node_CallFunction_128", "pin_name": "Substring", "value": "LedgeSeeking"}]})
for nid, pin in (("K2Node_CallFunction_132", "A"), ("K2Node_CallFunction_132", "B"),
                 ("K2Node_CallFunction_133", "A"), ("K2Node_IfThenElse_20", "Condition")):
    call("blueprint_query", "disconnect_pins", {"asset_path": BP, "graph_name": "EventGraph",
                                                "node_id": nid, "pin_name": pin})
conns = [
    # 정지 = OR(Idle, LedgeSeeking)
    {"source_node": "K2Node_CallFunction_131", "source_pin": "ReturnValue", "target_node": "K2Node_CallFunction_132", "target_pin": "A"},
    {"source_node": "K2Node_CallFunction_128", "source_pin": "ReturnValue", "target_node": "K2Node_CallFunction_132", "target_pin": "B"},
    {"source_node": "K2Node_CallFunction_132", "source_pin": "ReturnValue", "target_node": "K2Node_IfThenElse_20", "target_pin": "Condition"},
    # 이탈 = OR(End, BackwardJump)   (133.B <- 130 은 기존 유지)
    {"source_node": "K2Node_CallFunction_129", "source_pin": "ReturnValue", "target_node": "K2Node_CallFunction_133", "target_pin": "A"},
]
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": "EventGraph", "connections": conns})
f = [x for x in (rc.get("results") or []) if not x.get("success", True)]
LOG["fails"] += f
LOG["steps"].append("EventGraph rewired (%d fails)" % len(f))

# ── 변경 2: WriteIdleCurves 벽 분기 ──
nodes_spec = [
    {"temp_id": "gon", "node_type": "CallFunction", "function_name": "GetObjectName", "target_class": "KismetSystemLibrary", "position": [-600, 400]},
    {"temp_id": "con", "node_type": "CallFunction", "function_name": "Contains", "target_class": "KismetStringLibrary", "position": [-380, 400]},
    {"temp_id": "sel", "node_type": "CallFunction", "function_name": "SelectFloat", "target_class": KML, "position": [-160, 400]},
]
res = call("blueprint_query", "add_nodes_bulk", {"asset_path": BP, "graph_name": "WriteIdleCurves", "nodes": nodes_spec})
tmap = {}


def harvest(o):
    if isinstance(o, dict):
        if o.get("temp_id") and (o.get("node_id") or o.get("id")):
            tmap[o["temp_id"]] = o.get("node_id") or o.get("id")
        else:
            for v in o.values():
                harvest(v)
    elif isinstance(o, list):
        for e in o:
            harvest(e)


harvest(res)
if len(tmap) != 3:
    raise SystemExit("WriteIdleCurves 노드 생성 실패: " + json.dumps(res)[:300])

call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": BP, "graph_name": "WriteIdleCurves", "defaults": [
    {"node_id": tmap["con"], "pin_name": "Substring", "value": "Wallless"},
    {"node_id": tmap["con"], "pin_name": "bUseCase", "value": "false"},
    {"node_id": tmap["sel"], "pin_name": "A", "value": "0.0"},   # Wallless → 발 IK 끔
    {"node_id": tmap["sel"], "pin_name": "B", "value": "1.0"},   # 벽 있음 → 발 IK 1
]})
for nid in ("K2Node_CallFunction_5", "K2Node_CallFunction_7"):
    call("blueprint_query", "disconnect_pins", {"asset_path": BP, "graph_name": "WriteIdleCurves",
                                                "node_id": nid, "pin_name": "Value"})
conns2 = [
    {"source_node": "K2Node_FunctionEntry_0", "source_pin": "Seq", "target_node": tmap["gon"], "target_pin": "Object"},
    {"source_node": tmap["gon"], "source_pin": "ReturnValue", "target_node": tmap["con"], "target_pin": "SearchIn"},
    {"source_node": tmap["con"], "source_pin": "ReturnValue", "target_node": tmap["sel"], "target_pin": "bPickA"},
    {"source_node": tmap["sel"], "source_pin": "ReturnValue", "target_node": "K2Node_CallFunction_5", "target_pin": "Value"},
    {"source_node": tmap["sel"], "source_pin": "ReturnValue", "target_node": "K2Node_CallFunction_7", "target_pin": "Value"},
]
rc2 = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": "WriteIdleCurves", "connections": conns2})
f2 = [x for x in (rc2.get("results") or []) if not x.get("success", True)]
LOG["fails"] += f2
LOG["steps"].append("WriteIdleCurves wall-branch (%d fails)" % len(f2))
LOG["created"] = tmap

json.dump(LOG, open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/mod_reclassify.json", "w"), indent=1, ensure_ascii=False)
print("MOD_RECLASSIFY_DONE fails=%d" % len(LOG["fails"]))
for s in LOG["steps"]:
    print("  " + s)
if LOG["fails"]:
    print("  FAILS:", json.dumps(LOG["fails"])[:400])
