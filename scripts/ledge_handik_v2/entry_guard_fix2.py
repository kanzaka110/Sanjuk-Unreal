# v13c — bLedgeEventAnim 추적 플래그 (점프→렛지 진입 지연 수정)
# 원리: "지금 블렌드스택 애님 = EventTransit이 푸시한 것"일 때만 가드 홀드.
#  A. SetStateMachineBlendStackAnim(공용) 시작: bLedgeEventAnim=false 무조건 리셋
#  B. OnStateEntry_EventTransit 푸시 직후: bLedgeEventAnim=true
#  C. 가드 조건: and6 = (기존 and5) AND bLedgeEventAnim
# → 점프/폴 애님(Falling이 푸시, flag=false)은 렛지 도착 즉시 교체. 렛지 이벤트 애님만 보호.
# 롤백: A/B 스플라이스 exec 원복 각 1링크, C = and5→Condition 원복.
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
if "bLedgeEventAnim" not in existing:
    call("blueprint_query", "add_variable", {"asset_path": ABP, "name": "bLedgeEventAnim", "type": "bool",
                                             "category": "Ledge|TransitHold", "instance_editable": False})
    LOG["steps"].append("var: bLedgeEventAnim")

# ══ A. 공용 함수 시작에 리셋 스플라이스 ══
G1 = "SetStateMachineBlendStackAnim"
nodes = graph(G1)
ENTRY = "K2Node_FunctionEntry_0"
SEQ = "K2Node_ExecutionSequence_0"
if ENTRY not in nodes or SEQ not in nodes:
    raise SystemExit("A 앵커 소실")
if SEQ not in str(conn(nodes[ENTRY], "then")):
    raise SystemExit("A: Entry.then->%s (이미 스플라이스?)" % conn(nodes[ENTRY], "then"))
tmA = {}
harvest(call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": G1, "nodes": [
    {"temp_id": "setF", "node_type": "VariableSet", "variable_name": "bLedgeEventAnim", "position": [-384, -140]},
]}), tmA)
if "setF" not in tmA:
    raise SystemExit("A 노드 생성 실패")
if not graph(G1)[tmA["setF"]].get("pins"):
    raise SystemExit("A 빈 노드")
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": G1, "node_id": ENTRY, "pin_name": "then"})
rcA = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": G1, "connections": [
    {"source_node": ENTRY, "source_pin": "then", "target_node": tmA["setF"], "target_pin": "execute"},
    {"source_node": tmA["setF"], "source_pin": "then", "target_node": SEQ, "target_pin": "execute"},
]})
fA = [x for x in (rcA.get("results") or []) if not x.get("success", True)]
if fA:
    LOG["errors"].append(("A", fA))
LOG["steps"].append("A reset splice OK" if not fA else "A FAIL")

# ══ B. EventTransit 푸시 직후 true 스플라이스 ══
G2 = "OnStateEntry_EventTransit"
nodes = graph(G2)
CF0 = "K2Node_CallFunction_0"
RESULT = "K2Node_FunctionResult_0"
if CF0 not in nodes or RESULT not in nodes:
    raise SystemExit("B 앵커 소실")
if RESULT not in str(conn(nodes[CF0], "then")):
    raise SystemExit("B: CF0.then->%s" % conn(nodes[CF0], "then"))
tmB = {}
harvest(call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": G2, "nodes": [
    {"temp_id": "setT", "node_type": "VariableSet", "variable_name": "bLedgeEventAnim", "position": [420, 192]},
]}), tmB)
if "setT" not in tmB:
    raise SystemExit("B 노드 생성 실패")
if not graph(G2)[tmB["setT"]].get("pins"):
    raise SystemExit("B 빈 노드")
call("blueprint_query", "set_pin_default", {"asset_path": ABP, "graph_name": G2, "node_id": tmB["setT"],
                                            "pin_name": "bLedgeEventAnim", "value": "true"})
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": G2, "node_id": CF0, "pin_name": "then"})
rcB = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": G2, "connections": [
    {"source_node": CF0, "source_pin": "then", "target_node": tmB["setT"], "target_pin": "execute"},
    {"source_node": tmB["setT"], "source_pin": "then", "target_node": RESULT, "target_pin": "execute"},
]})
fB = [x for x in (rcB.get("results") or []) if not x.get("success", True)]
if fB:
    LOG["errors"].append(("B", fB))
LOG["steps"].append("B push-true splice OK" if not fB else "B FAIL")

# ══ C. 가드 조건 확장 ══
nodes = graph(G2)
brA = None
for nid, n in nodes.items():
    if n["class"] == "K2Node_IfThenElse":
        brA = nid
cond = conn(nodes[brA], "Condition")
if not cond:
    raise SystemExit("C: Condition 미연결")
and5 = cond[0].split(".")[0]
tmC = {}
harvest(call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": G2, "nodes": [
    {"temp_id": "gFlag", "node_type": "VariableGet", "variable_name": "bLedgeEventAnim", "position": [140, 1020]},
    {"temp_id": "and6", "node_type": "CallFunction", "function_name": "BooleanAND", "target_class": KML, "position": [300, 960]},
]}), tmC)
if len(tmC) != 2:
    raise SystemExit("C 노드 생성 실패: " + str(tmC))
nn = graph(G2)
for tid in tmC:
    if not nn[tmC[tid]].get("pins"):
        raise SystemExit("C 빈 노드: " + tid)
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": G2, "node_id": brA, "pin_name": "Condition"})
rcC = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": G2, "connections": [
    {"source_node": and5, "source_pin": "ReturnValue", "target_node": tmC["and6"], "target_pin": "A"},
    {"source_node": tmC["gFlag"], "source_pin": "bLedgeEventAnim", "target_node": tmC["and6"], "target_pin": "B"},
    {"source_node": tmC["and6"], "source_pin": "ReturnValue", "target_node": brA, "target_pin": "Condition"},
]})
fC = [x for x in (rcC.get("results") or []) if not x.get("success", True)]
if fC:
    LOG["errors"].append(("C", fC))
LOG["steps"].append("C guard AND flag OK" if not fC else "C FAIL")

with open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/entry_guard_fix2.json", "w") as fp:
    json.dump(LOG, fp, indent=1, ensure_ascii=False)
print("ENTRY_GUARD_FIX2_DONE errors=%s" % ("none" if not LOG["errors"] else json.dumps(LOG["errors"], ensure_ascii=False)[:500]))
