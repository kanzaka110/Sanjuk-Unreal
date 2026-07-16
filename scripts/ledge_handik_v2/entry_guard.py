# v13 — OnStateEntry_EventTransit 재진입 가드 (시퀀스 절단 근본 수정)
# 실측 근거: 절단 = T44(FromEvent→EventTransit) mv!=prevMv 하강에지 재진입 → OnStateEntry가 무조건 재픽.
# 가드: skip = LedgeMoveData.bActive AND !bTransitMoving AND !TransitingToNextLedge
#              AND !BlendStackInputs.Loop AND !IsStateMachineBlendStackAnimInBlendOut()
# skip=true → Return 직행(애님 유지). 롤백 = Entry.then→VS_0 원복 1링크 + 가드 노드 삭제.
# ⚠ 로컬 python 전용 — 에디터 콘솔(py) 실행 금지 (자기 서버 데드락).
import json, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
G = "OnStateEntry_EventTransit"
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


def graph_nodes():
    g = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": G})
    return {n["id"]: n for n in g["nodes"]}


def pins(n):
    return {p["name"]: p for p in n.get("pins", [])}


# ── 프리플라이트: 앵커 + 기존 배선 확인 ──
nodes = graph_nodes()
ENTRY = "K2Node_FunctionEntry_0"
VS0 = "K2Node_VariableSet_0"     # Set TargetRotationDeltaAtBeginState
CF0 = "K2Node_CallFunction_0"    # SetStateMachineBlendStackAnim
RESULT = "K2Node_FunctionResult_0"
miss = [x for x in (ENTRY, VS0, CF0, RESULT) if x not in nodes]
if miss:
    raise SystemExit("앵커 소실: " + str(miss))
ent_then = pins(nodes[ENTRY])["then"].get("connected_to") or []
if not any(VS0 in c for c in ent_then):
    raise SystemExit("Entry.then 배선이 예상과 다름 (이미 가드 적용?): " + str(ent_then))
LOG["steps"].append("preflight OK")

# ── 노드 생성 ──
spec = [
    {"temp_id": "brA", "node_type": "Branch", "position": [-380, -96]},
    {"temp_id": "gLMD", "node_type": "VariableGet", "variable_name": "LedgeMoveData", "position": [-980, 560]},
    {"temp_id": "brkLMD", "node_type": "BreakStruct", "struct_type": "SBLedgeMoveData", "position": [-760, 560]},
    {"temp_id": "gMv", "node_type": "VariableGet", "variable_name": "bTransitMoving", "position": [-980, 700]},
    {"temp_id": "not1", "node_type": "CallFunction", "function_name": "Not_PreBool", "target_class": KML, "position": [-760, 700]},
    {"temp_id": "gTr", "node_type": "VariableGet", "variable_name": "TransitingToNextLedge", "position": [-980, 780]},
    {"temp_id": "not2", "node_type": "CallFunction", "function_name": "Not_PreBool", "target_class": KML, "position": [-760, 780]},
    {"temp_id": "gBSI", "node_type": "VariableGet", "variable_name": "BlendStackInputs", "position": [-980, 860]},
    {"temp_id": "brkBSI", "node_type": "BreakStruct", "struct_type": "S_BlendStackInputs", "position": [-760, 860]},
    {"temp_id": "not3", "node_type": "CallFunction", "function_name": "Not_PreBool", "target_class": KML, "position": [-500, 860]},
    {"temp_id": "callBO", "node_type": "CallFunction", "function_name": "IsStateMachineBlendStackAnimInBlendOut", "target_class": "PC_01_ABP_C", "position": [-980, 960]},
    {"temp_id": "not4", "node_type": "CallFunction", "function_name": "Not_PreBool", "target_class": KML, "position": [-760, 960]},
    {"temp_id": "and1", "node_type": "CallFunction", "function_name": "BooleanAND", "target_class": KML, "position": [-500, 620]},
    {"temp_id": "and2", "node_type": "CallFunction", "function_name": "BooleanAND", "target_class": KML, "position": [-340, 690]},
    {"temp_id": "and3", "node_type": "CallFunction", "function_name": "BooleanAND", "target_class": KML, "position": [-180, 760]},
    {"temp_id": "and4", "node_type": "CallFunction", "function_name": "BooleanAND", "target_class": KML, "position": [-20, 830]},
]
tm = {}
res = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": G, "nodes": spec})
harvest(res, tm)
if len(tm) != len(spec):
    made = set(tm)
    raise SystemExit("노드 %d/%d missing=%s" % (len(tm), len(spec), [n["temp_id"] for n in spec if n["temp_id"] not in made]))
LOG["steps"].append("nodes: %d" % len(tm))

# ── 생성 노드 핀 검증 (빈노드/폴백 함정) ──
nodes = graph_nodes()
def outpin(tid, name_prefix):
    n = nodes[tm[tid]]
    for p in n.get("pins", []):
        if p["direction"] == "output" and p["name"].startswith(name_prefix):
            return p["name"]
    raise SystemExit("%s: output pin '%s*' 없음 pins=%s" % (tid, name_prefix, [p["name"] for p in n.get("pins", [])]))
def inpin(tid, name_prefix):
    n = nodes[tm[tid]]
    for p in n.get("pins", []):
        if p["direction"] == "input" and p["name"].startswith(name_prefix):
            return p["name"]
    raise SystemExit("%s: input pin '%s*' 없음 pins=%s" % (tid, name_prefix, [p["name"] for p in n.get("pins", [])]))

for tid in tm:
    if not nodes[tm[tid]].get("pins"):
        raise SystemExit("빈 노드(핀0): " + tid)

p_gLMD = outpin("gLMD", "LedgeMoveData")
p_brkLMD_in = inpin("brkLMD", "SBLedgeMoveData")
p_bActive = outpin("brkLMD", "bActive")
p_gMv = outpin("gMv", "bTransitMoving")
p_gTr = outpin("gTr", "TransitingToNextLedge")
p_gBSI = outpin("gBSI", "BlendStackInputs")
p_brkBSI_in = inpin("brkBSI", "S_BlendStackInputs")
p_loop = outpin("brkBSI", "Loop_")
p_callBO = outpin("callBO", "ReturnValue")
LOG["steps"].append("pin verify OK (Loop=%s)" % p_loop)

# ── 배선 ──
conns = [
    {"source_node": tm["gLMD"], "source_pin": p_gLMD, "target_node": tm["brkLMD"], "target_pin": p_brkLMD_in},
    {"source_node": tm["brkLMD"], "source_pin": p_bActive, "target_node": tm["and1"], "target_pin": "A"},
    {"source_node": tm["gMv"], "source_pin": p_gMv, "target_node": tm["not1"], "target_pin": "A"},
    {"source_node": tm["not1"], "source_pin": "ReturnValue", "target_node": tm["and1"], "target_pin": "B"},
    {"source_node": tm["gTr"], "source_pin": p_gTr, "target_node": tm["not2"], "target_pin": "A"},
    {"source_node": tm["and1"], "source_pin": "ReturnValue", "target_node": tm["and2"], "target_pin": "A"},
    {"source_node": tm["not2"], "source_pin": "ReturnValue", "target_node": tm["and2"], "target_pin": "B"},
    {"source_node": tm["gBSI"], "source_pin": p_gBSI, "target_node": tm["brkBSI"], "target_pin": p_brkBSI_in},
    {"source_node": tm["brkBSI"], "source_pin": p_loop, "target_node": tm["not3"], "target_pin": "A"},
    {"source_node": tm["and2"], "source_pin": "ReturnValue", "target_node": tm["and3"], "target_pin": "A"},
    {"source_node": tm["not3"], "source_pin": "ReturnValue", "target_node": tm["and3"], "target_pin": "B"},
    {"source_node": tm["callBO"], "source_pin": p_callBO, "target_node": tm["not4"], "target_pin": "A"},
    {"source_node": tm["and3"], "source_pin": "ReturnValue", "target_node": tm["and4"], "target_pin": "A"},
    {"source_node": tm["not4"], "source_pin": "ReturnValue", "target_node": tm["and4"], "target_pin": "B"},
    {"source_node": tm["and4"], "source_pin": "ReturnValue", "target_node": tm["brA"], "target_pin": "Condition"},
]
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": G, "node_id": ENTRY, "pin_name": "then"})
conns += [
    {"source_node": ENTRY, "source_pin": "then", "target_node": tm["brA"], "target_pin": "execute"},
    {"source_node": tm["brA"], "source_pin": "then", "target_node": RESULT, "target_pin": "execute"},
    {"source_node": tm["brA"], "source_pin": "else", "target_node": VS0, "target_pin": "execute"},
]
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": G, "connections": conns})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append(fails)
LOG["steps"].append("links: %d req %d fail" % (len(conns), len(fails)))

with open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/entry_guard.json", "w") as fp:
    json.dump(LOG, fp, indent=1, ensure_ascii=False)
print("ENTRY_GUARD_DONE errors=%s" % ("none" if not LOG["errors"] else json.dumps(LOG["errors"], ensure_ascii=False)[:400]))
