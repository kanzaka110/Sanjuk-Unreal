# v5b: Array_Get 재스폰 — CallArrayFunction 3단 레시피 (§2)
#   CallFunction 스폰본(K2Node_CallFunction_137)은 와일드카드 영구 미해결 -> 제거 후 재작업
import json
import urllib.request
import atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/SBWind_Weight_TEST01_Map"
EG = "EventGraph"
BAD = "K2Node_CallFunction_137"
GARR = "K2Node_VariableGet_27"
MOD = "K2Node_CallFunction_68"
SETSTR = "K2Node_VariableSet_11"
D2S = "K2Node_CallFunction_125"
FREF = "(MemberParent=\"/Script/CoreUObject.Class'/Script/Engine.KismetArrayLibrary'\",MemberName=\"Array_Get\")"
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
        raise RuntimeError(action + ": " + txt[:400])
    return json.loads(txt)


def connect(cs: list) -> int:
    rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": EG, "connections": cs})
    fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    if fails:
        LOG["errors"].append({"conns": fails})
    return len(fails)


def pins(nid: str) -> list:
    det = call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": EG, "node_id": nid})
    return [(p.get("name"), p.get("type")) for p in (det.get("pins") or [])]


# 1) 잘못된 노드 제거
call("blueprint_query", "remove_node", {"asset_path": BP, "graph_name": EG, "node_id": BAD})
LOG["steps"].append("bad Array_Get 제거")

# 2) CallArrayFunction 3단 스폰
r = call("blueprint_query", "add_node",
         {"asset_path": BP, "graph_name": EG, "node_type": "CallArrayFunction", "position": [-400, 1650]})
aget = r.get("node_id") or r.get("id")
call("blueprint_query", "set_node_property",
     {"asset_path": BP, "graph_name": EG, "node_id": aget, "property_name": "FunctionReference", "value": FREF})
call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": EG, "node_id": aget})
LOG["steps"].append("aget=%s pins=%s" % (aget, pins(aget)))

# 3) 배열 핀 먼저 연결 (타입 전파) -> 확인 -> 나머지
f1 = connect([{"source_node": GARR, "source_pin": "WindStepValues", "target_node": aget, "target_pin": "TargetArray"}])
after = pins(aget)
LOG["steps"].append("배열 연결 후 pins=%s" % after)
item_t = dict(after).get("Item", "?")
assert "wildcard" not in item_t, "타입 전파 실패: Item=%s" % item_t

f2 = connect([
    {"source_node": MOD, "source_pin": "ReturnValue", "target_node": aget, "target_pin": "Index"},
    {"source_node": aget, "source_pin": "Item", "target_node": SETSTR, "target_pin": "WindStrength"},
    {"source_node": aget, "source_pin": "Item", "target_node": D2S, "target_pin": "InDouble"},
])
LOG["steps"].append("connects fail=%d+%d" % (f1, f2))
assert f1 + f2 == 0, "배선 실패"

cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:400])
