# v14 — 손별 Dest 홀드 게이트 (이동시작 α=1 프레임의 130cm 타깃 점프 당김 수정)
# 실측: mv 상승 프레임에 Dest가 도착그립으로 점프하는데 α 릴리즈는 1~3프레임 뒤 → 손이 1틱 끌림.
# hold = IsMoving(Entry.InputPin2) AND GetCurveValue(ledge_hand_ik_x) > 0.5 → 직전 Dest 유지(구그립 핀).
# 릴리즈(커브<0.5) 시 새 Dest 통과, 플랜트 재상승 시엔 이미 새 값 저장 → 연속. 정지(mv=0)=무조건 통과.
# 롤백: VS_0/VS_1 데이터 핀을 원래 Knot 소스로 재연결 + 신규 10노드 삭제.
# ⚠ 로컬 python 전용 — 에디터 콘솔(py) 실행 금지.
import json, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
G = "Ledge_HandTarget"
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


def graph():
    return {n["id"]: n for n in call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": G})["nodes"]}


def pins(n):
    return {p["name"]: p for p in n.get("pins", [])}


def conn(ns, nid, pin):
    return (pins(ns[nid]).get(pin, {}).get("connected_to") or [])


ns = graph()
ENT = [i for i, n in ns.items() if n["class"] == "K2Node_FunctionEntry"][0]
VS0 = VS1 = None
for i, n in ns.items():
    if n["class"] == "K2Node_VariableSet":
        t = n.get("title", "")
        if "LedgeHandDestL" in t:
            VS0 = i
        elif "LedgeHandDestR" in t:
            VS1 = i
assert VS0 and VS1, (VS0, VS1)
srcL = conn(ns, VS0, "LedgeHandDestL")
srcR = conn(ns, VS1, "LedgeHandDestR")
assert srcL and srcR, "SetDest 데이터 소스 없음"
srcL_n, srcL_p = srcL[0].split(".")
srcR_n, srcR_p = srcR[0].split(".")
LOG["steps"].append("src L=%s R=%s" % (srcL[0], srcR[0]))

spec = []
for side, y in (("L", 3600), ("R", 3900)):
    spec += [
        {"temp_id": "cv" + side, "node_type": "CallFunction", "function_name": "GetCurveValue", "position": [4200, y]},
        {"temp_id": "gt" + side, "node_type": "CallFunction", "function_name": "Greater_DoubleDouble", "target_class": KML, "position": [4400, y]},
        {"temp_id": "and" + side, "node_type": "CallFunction", "function_name": "BooleanAND", "target_class": KML, "position": [4560, y]},
        {"temp_id": "prev" + side, "node_type": "VariableGet", "variable_name": "LedgeHandDest" + side, "position": [4400, y + 90]},
        {"temp_id": "sel" + side, "node_type": "CallFunction", "function_name": "SelectVector", "target_class": KML, "position": [4720, y + 40]},
    ]
tm = {}
harvest(call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": G, "nodes": spec}), tm)
if len(tm) != len(spec):
    raise SystemExit("노드 %d/%d: %s" % (len(tm), len(spec), tm))
ns = graph()
for t in tm:
    if not ns[tm[t]].get("pins"):
        raise SystemExit("빈 노드: " + t)
# CurveName / 0.5 디폴트
call("blueprint_query", "set_pin_default", {"asset_path": ABP, "graph_name": G, "node_id": tm["cvL"], "pin_name": "CurveName", "value": "ledge_hand_ik_l"})
call("blueprint_query", "set_pin_default", {"asset_path": ABP, "graph_name": G, "node_id": tm["cvR"], "pin_name": "CurveName", "value": "ledge_hand_ik_r"})
for s in ("L", "R"):
    call("blueprint_query", "set_pin_default", {"asset_path": ABP, "graph_name": G, "node_id": tm["gt" + s], "pin_name": "B", "value": "0.5"})

conns = []
for s, srcn, srcp, vs, dpin in (("L", srcL_n, srcL_p, VS0, "LedgeHandDestL"), ("R", srcR_n, srcR_p, VS1, "LedgeHandDestR")):
    conns += [
        {"source_node": tm["cv" + s], "source_pin": "ReturnValue", "target_node": tm["gt" + s], "target_pin": "A"},
        {"source_node": ENT, "source_pin": "InputPin2", "target_node": tm["and" + s], "target_pin": "A"},
        {"source_node": tm["gt" + s], "source_pin": "ReturnValue", "target_node": tm["and" + s], "target_pin": "B"},
        {"source_node": tm["prev" + s], "source_pin": "LedgeHandDest" + s, "target_node": tm["sel" + s], "target_pin": "A"},
        {"source_node": srcn, "source_pin": srcp, "target_node": tm["sel" + s], "target_pin": "B"},
        {"source_node": tm["and" + s], "source_pin": "ReturnValue", "target_node": tm["sel" + s], "target_pin": "bPickA"},
    ]
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": G, "node_id": VS0, "pin_name": "LedgeHandDestL"})
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": G, "node_id": VS1, "pin_name": "LedgeHandDestR"})
conns += [
    {"source_node": tm["selL"], "source_pin": "ReturnValue", "target_node": VS0, "target_pin": "LedgeHandDestL"},
    {"source_node": tm["selR"], "source_pin": "ReturnValue", "target_node": VS1, "target_pin": "LedgeHandDestR"},
]
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": G, "connections": conns})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append(fails)
LOG["steps"].append("links: %d req %d fail" % (len(conns), len(fails)))
# 검증
ns = graph()
okL = tm["selL"] in str(conn(ns, VS0, "LedgeHandDestL"))
okR = tm["selR"] in str(conn(ns, VS1, "LedgeHandDestR"))
LOG["steps"].append("verify L=%s R=%s" % (okL, okR))
with open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/dest_hold.json", "w") as fp:
    json.dump(LOG, fp, indent=1, ensure_ascii=False)
print("DEST_HOLD_DONE errors=%s verify=%s/%s" % ("none" if not LOG["errors"] else json.dumps(LOG["errors"], ensure_ascii=False)[:300], okL, okR))
if not (okL and okR) or fails:
    raise SystemExit(1)
