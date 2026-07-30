# BP_GroomWindCap 패치: GroomAssetFilter — 지정 그룸 에셋(기본 PC_01_Hair_01_InGame)에만 캡 적용
# Tick 루프에서 현재 GroomAsset 이름을 매 프레임 비교 (런타임 InGame/Cinematic 스왑 대응).
# 필터 빈 문자열 = 전체 적용(기존 동작).
import json, urllib.request, atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Developers/SHIFTUP/CSH/BP_GroomWindCap"
EG = "EventGraph"
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
    if not nid:
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
        nid = hv(r)
    return nid


def node_pins(nid):
    det = call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": EG, "node_id": nid})
    return [p.get("name") for p in (det.get("pins") or det.get("node", {}).get("pins") or [])]


# ── 1) 변수 ──
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": BP}).get("variables", [])}
if "GroomAssetFilter" not in existing:
    call("blueprint_query", "add_variable",
         {"asset_path": BP, "name": "GroomAssetFilter", "type": "string",
          "default_value": "PC_01_Hair_01_InGame", "category": "GroomWindCap", "instance_editable": True})
    LOG["steps"].append("var GroomAssetFilter")

# ── 2) 대상 노드 탐색 (핀 구조 기반 §19) ──
g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": EG})
nodes = {n["id"]: n for n in g["nodes"]}
def pins(n): return {p["name"]: p for p in n.get("pins", [])}
wsSet = loopT = None
for nid, n in nodes.items():
    P = pins(n)
    if "VariableSet" in n.get("class", "") and "WindScale" in P and P.get("self", {}).get("type") == "object:SBGroomComponent":
        wsSet = nid
for nid, n in nodes.items():
    if "MacroInstance" not in n.get("class", ""):
        continue
    outs = pins(n).get("LoopBody", {}).get("connected_to") or []
    if any(s.split(".")[0] == wsSet for s in outs):
        loopT = nid
assert wsSet and loopT, "wsSet/loopT 미발견: %s %s" % (wsSet, loopT)
LOG["steps"].append("wsSet=%s loopT=%s" % (wsSet, loopT))

# ── 3) ext GroomAsset 게터 (§9) ──
r = call("blueprint_query", "add_node",
         {"asset_path": BP, "graph_name": EG, "node_type": "VariableGet",
          "variable_name": "GroomAsset", "target_class": "GroomComponent", "position": [1500, 1750]})
gaGet = node_id_of(r)
ok = False
for parent in ("/Script/HairStrandsCore.GroomComponent", "/Script/SB2.SBGroomComponent", "/Script/SB2.SBCharacterGroomComponent"):
    call("blueprint_query", "set_node_property",
         {"asset_path": BP, "graph_name": EG, "node_id": gaGet,
          "property_name": "VariableReference", "value": '(MemberParent=%s,MemberName="GroomAsset",bSelfContext=False)' % parent})
    call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": EG, "node_id": gaGet})
    if "GroomAsset" in node_pins(gaGet):
        LOG["steps"].append("gaGet OK (%s)" % parent)
        ok = True
        break
assert ok, "GroomAsset 게터 수리 실패"

# ── 4) 비교 체인 스폰 ──
spec = [
    {"temp_id": "objName", "node_type": "CallFunction", "function_name": "GetObjectName", "target_class": "KismetSystemLibrary", "position": [1700, 1750]},
    {"temp_id": "getFilter", "node_type": "VariableGet", "variable_name": "GroomAssetFilter", "position": [1700, 1900]},
    {"temp_id": "eqName", "node_type": "CallFunction", "function_name": "EqualEqual_StrStr", "target_class": "KismetStringLibrary", "position": [1900, 1780]},
    {"temp_id": "eqEmpty", "node_type": "CallFunction", "function_name": "EqualEqual_StrStr", "target_class": "KismetStringLibrary", "position": [1900, 1930]},
    {"temp_id": "orB", "node_type": "CallFunction", "function_name": "BooleanOR", "target_class": "KismetMathLibrary", "position": [2080, 1850]},
    {"temp_id": "brMatch", "node_type": "Branch", "position": [1900, 1150]},
]
res = call("blueprint_query", "add_nodes_bulk", {"asset_path": BP, "graph_name": EG, "nodes": spec})
tm = {}
def hv(o):
    if isinstance(o, dict):
        if o.get("temp_id") and (o.get("node_id") or o.get("id")):
            tm[o["temp_id"]] = o.get("node_id") or o.get("id")
        else:
            for v in o.values(): hv(v)
    elif isinstance(o, list):
        for e in o: hv(e)
hv(res)
assert len(tm) == len(spec), "노드 %d/%d: %s" % (len(tm), len(spec), json.dumps(res)[:300])

rd = call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": BP, "graph_name": EG, "defaults": [
    {"node_id": tm["eqEmpty"], "pin_name": "B", "value": ""}]})

# ── 5) 연결 ──
conns = [
    {"source_node": loopT, "source_pin": "Array Element", "target_node": gaGet, "target_pin": "self"},
    {"source_node": gaGet, "source_pin": "GroomAsset", "target_node": tm["objName"], "target_pin": "Object"},
    {"source_node": tm["objName"], "source_pin": "ReturnValue", "target_node": tm["eqName"], "target_pin": "A"},
    {"source_node": tm["getFilter"], "source_pin": "GroomAssetFilter", "target_node": tm["eqName"], "target_pin": "B"},
    {"source_node": tm["getFilter"], "source_pin": "GroomAssetFilter", "target_node": tm["eqEmpty"], "target_pin": "A"},
    {"source_node": tm["eqName"], "source_pin": "ReturnValue", "target_node": tm["orB"], "target_pin": "A"},
    {"source_node": tm["eqEmpty"], "source_pin": "ReturnValue", "target_node": tm["orB"], "target_pin": "B"},
    {"source_node": tm["orB"], "source_pin": "ReturnValue", "target_node": tm["brMatch"], "target_pin": "Condition"},
]
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": EG, "connections": conns})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append({"conns": fails})

# exec 리와이어: loopT.LoopBody -> brMatch -> wsSet (§7 disconnect 선행)
call("blueprint_query", "disconnect_pins",
     {"asset_path": BP, "graph_name": EG,
      "source_node": loopT, "source_pin": "LoopBody", "target_node": wsSet, "target_pin": "execute"})
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": EG, "connections": [
    {"source_node": loopT, "source_pin": "LoopBody", "target_node": tm["brMatch"], "target_pin": "execute"},
    {"source_node": tm["brMatch"], "source_pin": "then", "target_node": wsSet, "target_pin": "execute"},
]})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append({"exec": fails})

# ── 6) 컴파일 + 저장 + 미연결 감사 ──
cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:300])
call("editor_query", "save_asset", {"asset_path": BP})
LOG["steps"].append("saved")
g2 = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": EG})
for n in g2["nodes"]:
    for p in n.get("pins", []):
        if p.get("direction") != "input" or p.get("connected_to"):
            continue
        nm = p.get("name")
        if nm in ("Condition", "Object", "Point", "Array", "TargetArray", "Index", "Item") or (nm == "self" and "VariableGet" in n.get("class", "")):
            LOG["errors"].append({"unconnected": [n["id"], n.get("title"), nm]})
