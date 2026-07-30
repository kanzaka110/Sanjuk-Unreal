# 레벨BP: SBVortexWindActor 3개의 강도 3성분(Tangential/Radial/Axial)을 5~20 랜덤 리롤 루프
#   BeginPlay 체인 꼬리에 삽입: [기존] -> vxLoop 진입
#   vxLoop: Sequence(3액터 × 3성분 Set) -> Delay(랜덤 hold) -> 루프백(자기 Sequence 재진입)
#   외부 컴포넌트 프로퍼티 Set = §9 T3D 수리, 액터 참조 = §10 K2Node_Literal
import json, urllib.request, atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Developers/SHIFTUP/CSH/SBWind_Weight_TEST01_Map"
EG = "EventGraph"
KML = "KismetMathLibrary"
VXC = "/Script/SB2.SBVortexWindComponent"
BASE = "/Game/Developers/SHIFTUP/CSH/SBWind_Weight_TEST01_Map.SBWind_Weight_TEST01_Map:PersistentLevel."
ACTORS = [BASE + "SBVortexWindActor_UAID_30560F6BCAE5D3F202_1767808275",
          BASE + "SBVortexWindActor_UAID_30560F6BCAE5D3F202_1767809276",
          BASE + "SBVortexWindActor_UAID_30560F6BCAE5D3F202_1767810277"]
FIELDS = ["TangentialStrength", "RadialStrength", "AxialStrength"]
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


def add(ntype, x, y, **kw):
    p = {"asset_path": BP, "graph_name": EG, "node_type": ntype, "position": [x, y]}
    p.update(kw)
    return nid_of(call("blueprint_query", "add_node", p))


def pins_of(nid):
    det = call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": EG, "node_id": nid})
    return [p.get("name") for p in (det.get("pins") or det.get("node", {}).get("pins") or [])]


def pindef(nid, pin, val):
    call("blueprint_query", "set_pin_default", {"asset_path": BP, "graph_name": EG, "node_id": nid, "pin_name": pin, "value": val})


def connect(cs):
    rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": EG, "connections": cs})
    f = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    if f:
        LOG["errors"].append({"conns": f})
    return len(f)


# ═══ 1) 변수 (범위) ═══
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": BP}).get("variables", [])}
for nm, dv in (("VortexStrMin", "5.0"), ("VortexStrMax", "20.0"), ("VortexHoldMin", "3.0"), ("VortexHoldMax", "8.0")):
    if nm not in existing:
        call("blueprint_query", "add_variable",
             {"asset_path": BP, "name": nm, "type": "float", "default_value": dv,
              "category": "WindRandom|Vortex", "instance_editable": True})
LOG["steps"].append("vars ok")

# ═══ 2) BeginPlay 체인 꼬리 찾기 (열린 then) ═══
g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": EG})
nodes = {n["id"]: n for n in g["nodes"]}
def P(n): return {p["name"]: p for p in n.get("pins", [])}
begin = None
for nid, n in nodes.items():
    if "K2Node_Event" in n.get("class", "") and ("Begin Play" in (n.get("title") or "") or "BeginPlay" in (n.get("title") or "")):
        begin = nid
assert begin, "BeginPlay 미발견"
# BeginPlay 로부터 exec 그래프 순회해 마지막 열린 then 찾기
visited, tail = set(), None
cur = begin
while cur and cur not in visited:
    visited.add(cur)
    nxt = None
    for pin in ("then", "Completed", "execute"):
        pp = P(nodes[cur]).get(pin) if cur in nodes else None
        if pin in ("then", "Completed") and pp:
            ct = pp.get("connected_to") or []
            if ct:
                nxt = ct[0].split(".")[0]
                break
    if not nxt:
        tail = cur
        break
    cur = nxt
LOG["steps"].append("begin=%s tail=%s" % (begin, tail))

# ═══ 3) 노드 스폰 ═══
seq = add("Sequence", 200, 7000)
# Sequence 핀 확장 (기본 2 -> 필요 시)
seq_pins = pins_of(seq)
LOG["steps"].append("seq pins: %s" % seq_pins)

setters = []   # (setNode, litNode)
x = 500
for ai, apath in enumerate(ACTORS):
    lit = add("K2Node_Literal", x, 7400 + ai * 60)
    call("blueprint_query", "set_node_property", {"asset_path": BP, "graph_name": EG, "node_id": lit,
         "property_name": "ObjectRef", "value": apath})
    call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": EG, "node_id": lit})
    lp = [p for p in pins_of(lit) if p not in ("execute", "then")][0]
    gc = add("CallFunction", x + 200, 7400 + ai * 60, function_name="GetComponentByClass", target_class="Actor")
    pindef(gc, "ComponentClass", VXC)
    connect([{"source_node": lit, "source_pin": lp, "target_node": gc, "target_pin": "self"}])
    for fi, fld in enumerate(FIELDS):
        st = add("VariableSet", x + 450 + fi * 260, 7000 + ai * 200, variable_name=fld, target_class="SBVortexWindComponent")
        call("blueprint_query", "set_node_property", {"asset_path": BP, "graph_name": EG, "node_id": st,
             "property_name": "VariableReference",
             "value": '(MemberParent=%s,MemberName="%s",bSelfContext=False)' % (VXC, fld)})
        call("blueprint_query", "refresh_node", {"asset_path": BP, "graph_name": EG, "node_id": st})
        assert fld in pins_of(st), "setter %s 핀 실패" % fld
        rnd = add("CallFunction", x + 450 + fi * 260, 7120 + ai * 200, function_name="RandomFloatInRange", target_class=KML)
        gmin = add("VariableGet", x + 380 + fi * 260, 7230 + ai * 200, variable_name="VortexStrMin")
        gmax = add("VariableGet", x + 380 + fi * 260, 7290 + ai * 200, variable_name="VortexStrMax")
        connect([
            {"source_node": gmin, "source_pin": "VortexStrMin", "target_node": rnd, "target_pin": "Min"},
            {"source_node": gmax, "source_pin": "VortexStrMax", "target_node": rnd, "target_pin": "Max"},
            {"source_node": rnd, "source_pin": "ReturnValue", "target_node": st, "target_pin": fld},
            {"source_node": gc, "source_pin": "ReturnValue", "target_node": st, "target_pin": "self"},
        ])
        setters.append(st)
    x += 100
LOG["steps"].append("setters: %d" % len(setters))

# Delay + hold 랜덤
dl = add("CallFunction", 3000, 7000, function_name="Delay", target_class="KismetSystemLibrary")
hr = add("CallFunction", 2800, 7150, function_name="RandomFloatInRange", target_class=KML)
hmin = add("VariableGet", 2650, 7250, variable_name="VortexHoldMin")
hmax = add("VariableGet", 2650, 7310, variable_name="VortexHoldMax")
connect([
    {"source_node": hmin, "source_pin": "VortexHoldMin", "target_node": hr, "target_pin": "Min"},
    {"source_node": hmax, "source_pin": "VortexHoldMax", "target_node": hr, "target_pin": "Max"},
    {"source_node": hr, "source_pin": "ReturnValue", "target_node": dl, "target_pin": "Duration"},
])

# ═══ 4) exec 체인: tail -> setter들 직렬 -> Delay -> 첫 setter 루프백 ═══
ex = []
if tail:
    tail_pin = "then" if "then" in P(nodes[tail]) else "Completed"
    ex.append({"source_node": tail, "source_pin": tail_pin, "target_node": setters[0], "target_pin": "execute"})
for i in range(len(setters) - 1):
    ex.append({"source_node": setters[i], "source_pin": "then", "target_node": setters[i + 1], "target_pin": "execute"})
ex.append({"source_node": setters[-1], "source_pin": "then", "target_node": dl, "target_pin": "execute"})
ex.append({"source_node": dl, "source_pin": "then", "target_node": setters[0], "target_pin": "execute"})
f = connect(ex)
LOG["steps"].append("exec links: %d fail %d" % (len(ex), f))

# 미사용 Sequence 제거
call("blueprint_query", "remove_node", {"asset_path": BP, "graph_name": EG, "node_id": seq})

cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:300])
