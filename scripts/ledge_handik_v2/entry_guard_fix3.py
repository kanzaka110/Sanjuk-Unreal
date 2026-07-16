# v13e — 플래그 소스 교정 (프로브 실측: 렛지 이동/크로싱 애님 푸시자 = OnStateEntry_EventMove)
#  A. OnStateEntry_EventMove 푸시 직후에도 bLedgeEventAnim=true 스플라이스 → 가드 부활
#  B. IsStateMachineBlendStackAnimInBlendOut 문턱 Select 조건 = flag AND LedgeMoveData.bActive
#     (래더도 EventMove 사용 → bActive로 렛지 한정. 점프/폴 애님은 flag=false → 0.5 유지)
# 롤백: A = CF0.then→Result 원복 1링크, B = bPickA←VariableGet(bLedgeEventAnim) 원복.
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


# ══ A. OnStateEntry_EventMove: 푸시 직후 flag=true ══
G1 = "OnStateEntry_EventMove"
nodes = graph(G1)
CF0 = RESULT = None
for nid, n in nodes.items():
    if n["class"] == "K2Node_CallFunction" and n.get("function") == "SetStateMachineBlendStackAnim":
        CF0 = nid
    elif n["class"] == "K2Node_FunctionResult":
        RESULT = nid
if not (CF0 and RESULT):
    raise SystemExit("A 앵커 소실 CF0=%s RESULT=%s" % (CF0, RESULT))
already = [i for i, n in nodes.items() if n["class"] == "K2Node_VariableSet" and "bLedgeEventAnim" in n.get("title", "")]
if already:
    raise SystemExit("A 이미 적용됨: " + str(already))
after = conn(nodes[CF0], "then")
if RESULT not in str(after):
    raise SystemExit("A: CF0.then->%s (Result 직결 아님 — 구조 확인 필요)" % after)
tmA = {}
harvest(call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": G1, "nodes": [
    {"temp_id": "setT", "node_type": "VariableSet", "variable_name": "bLedgeEventAnim", "position": [420, 192]},
]}), tmA)
if "setT" not in tmA or not graph(G1)[tmA["setT"]].get("pins"):
    raise SystemExit("A 노드 생성 실패")
call("blueprint_query", "set_pin_default", {"asset_path": ABP, "graph_name": G1, "node_id": tmA["setT"],
                                            "pin_name": "bLedgeEventAnim", "value": "true"})
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": G1, "node_id": CF0, "pin_name": "then"})
rcA = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": G1, "connections": [
    {"source_node": CF0, "source_pin": "then", "target_node": tmA["setT"], "target_pin": "execute"},
    {"source_node": tmA["setT"], "source_pin": "then", "target_node": RESULT, "target_pin": "execute"},
]})
fA = [x for x in (rcA.get("results") or []) if not x.get("success", True)]
if fA:
    LOG["errors"].append(("A", fA))
LOG["steps"].append("A EventMove flag splice OK" if not fA else "A FAIL")

# ══ B. 문턱 Select 조건 = flag AND bActive ══
G2 = "IsStateMachineBlendStackAnimInBlendOut"
nodes = graph(G2)
sel = gflag = None
for nid, n in nodes.items():
    if n.get("function") == "SelectFloat":
        sel = nid
    elif n["class"] == "K2Node_VariableGet" and "bLedgeEventAnim" in n.get("title", ""):
        gflag = nid
if not (sel and gflag):
    raise SystemExit("B 앵커 소실 sel=%s gflag=%s" % (sel, gflag))
tmB = {}
harvest(call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": G2, "nodes": [
    {"temp_id": "gLMD", "node_type": "VariableGet", "variable_name": "LedgeMoveData", "position": [656, 480]},
    {"temp_id": "brkLMD", "node_type": "BreakStruct", "struct_type": "SBLedgeMoveData", "position": [860, 480]},
    {"temp_id": "andT", "node_type": "CallFunction", "function_name": "BooleanAND", "target_class": KML, "position": [1040, 440]},
]}), tmB)
if len(tmB) != 3:
    raise SystemExit("B 노드 생성 실패: " + str(tmB))
nn = graph(G2)
brk_in = None
for p in nn[tmB["brkLMD"]].get("pins", []):
    if p["direction"] == "input" and p["name"].startswith("SBLedgeMoveData"):
        brk_in = p["name"]
if not brk_in or not nn[tmB["gLMD"]].get("pins") or not nn[tmB["andT"]].get("pins"):
    raise SystemExit("B 핀 검증 실패")
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": G2, "node_id": sel, "pin_name": "bPickA"})
rcB = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": G2, "connections": [
    {"source_node": tmB["gLMD"], "source_pin": "LedgeMoveData", "target_node": tmB["brkLMD"], "target_pin": brk_in},
    {"source_node": gflag, "source_pin": "bLedgeEventAnim", "target_node": tmB["andT"], "target_pin": "A"},
    {"source_node": tmB["brkLMD"], "source_pin": "bActive", "target_node": tmB["andT"], "target_pin": "B"},
    {"source_node": tmB["andT"], "source_pin": "ReturnValue", "target_node": sel, "target_pin": "bPickA"},
]})
fB = [x for x in (rcB.get("results") or []) if not x.get("success", True)]
if fB:
    LOG["errors"].append(("B", fB))
LOG["steps"].append("B threshold flag AND bActive OK" if not fB else "B FAIL")

with open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/entry_guard_fix3.json", "w") as fp:
    json.dump(LOG, fp, indent=1, ensure_ascii=False)
print("ENTRY_GUARD_FIX3_DONE errors=%s" % ("none" if not LOG["errors"] else json.dumps(LOG["errors"], ensure_ascii=False)[:500]))
