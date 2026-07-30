# CH_Mutable_Baked: UseHairLeaderPose 를 실제 게이트로 살림 (Hair 전용, FaceFoliage 무영향)
#  A) SetLeaderPoseHair: IfThenElse_1.else -> [새 Branch(UseHairLeaderPose)]
#       then  -> CallFunction_1 (Hair<-Head, 기존)  -> CallFunction_8 (FaceFoliage, 기존)
#       else  -> 새 SetLeaderPose(Hair, None)       -> CallFunction_8 (동일 지점 합류)
#  B) UserConstructionScript: MacroInstance_0."Is Valid" -> [새 Branch]
#       then -> CallFunction_2 (Hair<-Head, 기존) / else -> 새 SetLeaderPose(Hair, None)
# 디폴트 UseHairLeaderPose=true → 기존 동작 100% 동일(회귀 없음)
import json, urllib.request, atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/Character/Generic/CH_Mutable_Baked"
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


def nid_of(r):
    return r.get("node_id") or r.get("id")


def add(graph, ntype, x, y, **kw):
    p = {"asset_path": BP, "graph_name": graph, "node_type": ntype, "position": [x, y]}
    p.update(kw)
    return nid_of(call("blueprint_query", "add_node", p))


def pins_of(graph, nid):
    det = call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": graph, "node_id": nid})
    return [p.get("name") for p in (det.get("pins") or det.get("node", {}).get("pins") or [])]


def connect(graph, cs):
    rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": graph, "connections": cs})
    f = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    if f:
        LOG["errors"].append({graph: f})
    return len(f)


def var_get(graph, name, x, y):
    nid = add(graph, "VariableGet", x, y, variable_name=name)
    if name not in pins_of(graph, nid):
        call("blueprint_query", "set_node_property",
             {"asset_path": BP, "graph_name": graph, "node_id": nid,
              "property_name": "VariableReference",
              "value": '(MemberName="%s",bSelfContext=True)' % name})
        call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": graph, "node_id": nid})
    assert name in pins_of(graph, nid), "%s 게터 실패 (%s)" % (name, pins_of(graph, nid))
    return nid


# ═══ 중복 실행 가드 ═══
g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": "SetLeaderPoseHair"})
brs = [n for n in g["nodes"] if "IfThenElse" in n.get("class", "")]
if len(brs) > 1:
    raise SystemExit("SetLeaderPoseHair 에 Branch가 %d개 — 이미 수정된 것으로 보임. 중단." % len(brs))

# ═══ A) SetLeaderPoseHair ═══
FN = "SetLeaderPoseHair"
HAIR_SET = "K2Node_CallFunction_1"      # Hair <- Head (기존)
FF_SET = "K2Node_CallFunction_8"        # FaceFoliage (합류점)
BR_MAIN = "K2Node_IfThenElse_1"         # Branch(IsAnimNext)
HAIR_GETTER = "K2Node_VariableGet_9"    # Get Hair (기존, 데이터 핀 재사용)

# 사전 검증
gn = {n["id"]: n for n in g["nodes"]}
assert all(k in gn for k in (HAIR_SET, FF_SET, BR_MAIN, HAIR_GETTER)), "앵커 노드 누락"
def P(n): return {p["name"]: p for p in n.get("pins", [])}
assert (P(gn[HAIR_SET]).get("execute", {}).get("connected_to") or []) == [BR_MAIN + ".else"], "HAIR_SET exec 소스 불일치"
LOG["steps"].append("A 프리플라이트 OK")

brGate = add(FN, "Branch", -520, 780)
useGet = var_get(FN, "UseHairLeaderPose", -740, 900)
newSet = add(FN, "CallFunction", -300, 900, function_name="SetLeaderPoseComponent", target_class="SkinnedMeshComponent")
LOG["steps"].append("A 노드: brGate=%s useGet=%s newSet=%s" % (brGate, useGet, newSet))

call("blueprint_query", "disconnect_pins",
     {"asset_path": BP, "graph_name": FN,
      "source_node": BR_MAIN, "source_pin": "else", "target_node": HAIR_SET, "target_pin": "execute"})
f = connect(FN, [
    {"source_node": useGet, "source_pin": "UseHairLeaderPose", "target_node": brGate, "target_pin": "Condition"},
    {"source_node": BR_MAIN, "source_pin": "else", "target_node": brGate, "target_pin": "execute"},
    {"source_node": brGate, "source_pin": "then", "target_node": HAIR_SET, "target_pin": "execute"},
    {"source_node": brGate, "source_pin": "else", "target_node": newSet, "target_pin": "execute"},
    {"source_node": HAIR_GETTER, "source_pin": "Hair", "target_node": newSet, "target_pin": "self"},
    {"source_node": newSet, "source_pin": "then", "target_node": FF_SET, "target_pin": "execute"},
])
LOG["steps"].append("A 링크 fail=%d" % f)

# ═══ B) UserConstructionScript ═══
UCS = "UserConstructionScript"
u = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": UCS})
un = {n["id"]: n for n in u["nodes"]}
UHAIR_SET = "K2Node_CallFunction_2"     # Hair <- Head (기존)
src = (P(un[UHAIR_SET]).get("execute", {}).get("connected_to") or [None])[0]
assert src, "UCS Hair set exec 소스 없음"
src_node, src_pin = src.split(".")
LOG["steps"].append("B exec 소스: %s.%s" % (src_node, src_pin))
# Hair 게터 (기존 것 재사용)
uhair = (P(un[UHAIR_SET]).get("self", {}).get("connected_to") or [None])[0]
assert uhair, "UCS Hair 게터 없음"
uhair_node, uhair_pin = uhair.split(".")

brGate2 = add(UCS, "Branch", 400, 1200)
useGet2 = var_get(UCS, "UseHairLeaderPose", 180, 1320)
newSet2 = add(UCS, "CallFunction", 640, 1320, function_name="SetLeaderPoseComponent", target_class="SkinnedMeshComponent")
call("blueprint_query", "disconnect_pins",
     {"asset_path": BP, "graph_name": UCS,
      "source_node": src_node, "source_pin": src_pin, "target_node": UHAIR_SET, "target_pin": "execute"})
f2 = connect(UCS, [
    {"source_node": useGet2, "source_pin": "UseHairLeaderPose", "target_node": brGate2, "target_pin": "Condition"},
    {"source_node": src_node, "source_pin": src_pin, "target_node": brGate2, "target_pin": "execute"},
    {"source_node": brGate2, "source_pin": "then", "target_node": UHAIR_SET, "target_pin": "execute"},
    {"source_node": brGate2, "source_pin": "else", "target_node": newSet2, "target_pin": "execute"},
    {"source_node": uhair_node, "source_pin": uhair_pin, "target_node": newSet2, "target_pin": "self"},
])
LOG["steps"].append("B 링크 fail=%d" % f2)

cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:400])
