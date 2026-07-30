# PC_01_BP ApplyGroomWindCap: 이름 필터 -> 그룸 에셋 등록 배열(TargetGroomAssets)로 교체
# 규칙: Contains(TargetGroomAssets, 현재 GroomAsset) OR 배열 비었으면 전체 적용
# 제거: GetObjectName/GroomAssetFilter/EqualEqual_StrStr x2/BooleanOR(구) + GroomAssetFilter 변수
import json, urllib.request, atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
FN = "ApplyGroomWindCap"
KAL_REF = "(MemberParent=\"/Script/CoreUObject.Class'/Script/Engine.KismetArrayLibrary'\",MemberName=\"%s\")"
INGAME = "/Script/HairStrandsCore.GroomAsset'/Game/Art/Character/PC/PC_01/Equipment/Hair/PC_01_Hair_01/PC_01_Hair_01_InGame.PC_01_Hair_01_InGame'"
LOG = {"steps": [], "errors": []}
atexit.register(lambda: print(json.dumps(LOG, ensure_ascii=False, indent=1)))


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


def node_id_of(r):
    nid = r.get("node_id") or r.get("id")
    if nid:
        return nid
    def hv(o):
        if isinstance(o, dict):
            if o.get("node_id") or o.get("id"):
                return o.get("node_id") or o.get("id")
            for v in o.values():
                x = hv(v)
                if x:
                    return x
        elif isinstance(o, list):
            for e in o:
                x = hv(e)
                if x:
                    return x
    return hv(r)


def array_fn(fn_name, x, y):
    r = call("blueprint_query", "add_node",
             {"asset_path": BP, "graph_name": FN, "node_type": "CallArrayFunction", "position": [x, y]})
    nid = node_id_of(r)
    call("blueprint_query", "set_node_property",
         {"asset_path": BP, "graph_name": FN, "node_id": nid,
          "property_name": "FunctionReference", "value": KAL_REF % fn_name})
    call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": FN, "node_id": nid})
    return nid


# ═══ 1) 변수 ═══
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": BP}).get("variables", [])}
if "TargetGroomAssets" not in existing:
    call("blueprint_query", "add_variable",
         {"asset_path": BP, "name": "TargetGroomAssets", "type": "array:object:GroomAsset",
          "category": "Hair|Groom Wind Cap", "instance_editable": True})
    LOG["steps"].append("var TargetGroomAssets")

# ═══ 2) 기존 필터 노드 탐색 ═══
g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
nodes = {n["id"]: n for n in g["nodes"]}
def pins(n): return {p["name"]: p for p in n.get("pins", [])}
objName = getFilter = eqName = eqEmpty = orOld = brMatch = gaGet = None
for nid, n in nodes.items():
    t = (n.get("title") or "")
    P = pins(n)
    if "Get Object Name" in t:
        objName = nid
    if "VariableGet" in n.get("class", "") and "GroomAssetFilter" in P:
        getFilter = nid
    if "GroomAsset" in P and "VariableGet" in n.get("class", "") and P.get("self", {}).get("type", "").startswith("object:") and "GroomAssetFilter" not in P:
        gaGet = nid
    if "IfThenElse" in n.get("class", ""):
        cond = (P.get("Condition", {}).get("connected_to") or [""])[0]
        src = nodes.get(cond.split(".")[0], {})
        if "OR" in (src.get("title") or ""):
            brMatch = nid
            orOld = cond.split(".")[0]
eqs = [nid for nid, n in nodes.items() if "Equal Exactly (String)" in (n.get("title") or "")]
LOG["steps"].append("found: objName=%s getFilter=%s gaGet=%s orOld=%s brMatch=%s eqs=%s" % (objName, getFilter, gaGet, orOld, brMatch, eqs))
assert all([objName, getFilter, gaGet, orOld, brMatch]) and len(eqs) == 2, "탐색 실패"

# ═══ 3) 구 필터 노드 제거 ═══
for nid in [objName, getFilter, orOld] + eqs:
    call("blueprint_query", "remove_node", {"asset_path": BP, "graph_name": FN, "node_id": nid})
LOG["steps"].append("old filter nodes removed (5)")

# ═══ 4) 신규: 등록 배열 판정 ═══
r = call("blueprint_query", "add_node",
         {"asset_path": BP, "graph_name": FN, "node_type": "VariableGet",
          "variable_name": "TargetGroomAssets", "position": [2350, 1650]})
getTargets = node_id_of(r)
cont = array_fn("Array_Contains", 2650, 1560)
lenT = array_fn("Array_Length", 2650, 1750)
r = call("blueprint_query", "add_node",
         {"asset_path": BP, "graph_name": FN, "node_type": "CallFunction",
          "function_name": "EqualEqual_IntInt", "target_class": "KismetMathLibrary", "position": [2850, 1750]})
eq0 = node_id_of(r)
r = call("blueprint_query", "add_node",
         {"asset_path": BP, "graph_name": FN, "node_type": "CallFunction",
          "function_name": "BooleanOR", "target_class": "KismetMathLibrary", "position": [2900, 1600]})
orNew = node_id_of(r)
call("blueprint_query", "set_pin_default", {"asset_path": BP, "graph_name": FN, "node_id": eq0, "pin_name": "B", "value": "0"})

conns = [
    # 배열핀 먼저 (와일드카드 전파 §2)
    {"source_node": getTargets, "source_pin": "TargetGroomAssets", "target_node": cont, "target_pin": "TargetArray"},
    {"source_node": getTargets, "source_pin": "TargetGroomAssets", "target_node": lenT, "target_pin": "TargetArray"},
    {"source_node": gaGet, "source_pin": "GroomAsset", "target_node": cont, "target_pin": "ItemToFind"},
    {"source_node": lenT, "source_pin": "ReturnValue", "target_node": eq0, "target_pin": "A"},
    {"source_node": cont, "source_pin": "ReturnValue", "target_node": orNew, "target_pin": "A"},
    {"source_node": eq0, "source_pin": "ReturnValue", "target_node": orNew, "target_pin": "B"},
    {"source_node": orNew, "source_pin": "ReturnValue", "target_node": brMatch, "target_pin": "Condition"},
]
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": FN, "connections": conns})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append({"conns": fails})
LOG["steps"].append("links: %d req %d fail" % (len(conns), len(fails)))

# ═══ 5) 구 변수 제거 + 디폴트 등록 ═══
call("blueprint_query", "remove_variable", {"asset_path": BP, "name": "GroomAssetFilter"})
LOG["steps"].append("GroomAssetFilter var removed")
try:
    call("blueprint_query", "set_variable_defaults",
         {"asset_path": BP, "variable_name": "TargetGroomAssets", "default_value": '("%s")' % INGAME})
    LOG["steps"].append("default registered: InGame")
except RuntimeError as e:
    LOG["errors"].append({"default_set": str(e)[:200]})

# ═══ 6) 컴파일 + 감사 ═══
cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:300])
g2 = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": FN})
for n in g2["nodes"]:
    for p in n.get("pins", []):
        if p.get("direction") != "input" or p.get("connected_to"):
            continue
        nm = p.get("name")
        if nm in ("Condition", "Object", "Point", "Array", "TargetArray", "Index", "Item", "ItemToFind", "NewItem") or (nm == "self" and "VariableGet" in n.get("class", "")):
            LOG["errors"].append({"unconnected": [n["id"], (n.get("title") or "")[:40], nm]})
