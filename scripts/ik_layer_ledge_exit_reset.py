# PC_01_AnimLayer_IK 렛지 이탈 리셋 — 렛지->월런 IK 꼬임 수정 (2026-08-06)
#   실측 근거: 렛지 이탈 시 LedgeHandIKAlphaL/R 등이 이탈 순간 값으로 동결 잔존 (pie_smoke_9, 2회 재현)
#   원인: 렛지 갱신/리셋 코드 전부 Switch(ESBCustomMovementMode) SB_MOVE_Ledge 케이스 안 -> 이탈하면 실행 기회 없음
#   설계(enum 리터럴 회피 = 플래그 방식):
#     ①Ledge 케이스 헤드에 Set LedgeCaseTick=true 스플라이스
#     ②Sequence then_3(빈 핀): Branch(LedgeCaseTick) then->플래그 클리어(렛지 중) /
#       else->렛지 미러 알파 7종 0 + LedgePhysWanted=false + Branch(LedgePhysProfileOn)->기존 Kinematic 오프 시퀀스(CF_18) 팬인
import json, urllib.request, atexit

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"
G = "EventGraph"
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


def add(ntype, x, y, **kw):
    p = {"asset_path": BP, "graph_name": G, "node_type": ntype, "position": [x, y]}
    p.update(kw)
    return node_id_of(call("blueprint_query", "add_node", p))


def pindef(nid, pin, val):
    call("blueprint_query", "set_pin_default", {"asset_path": BP, "graph_name": G, "node_id": nid, "pin_name": pin, "value": val})


def connect(cs):
    rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": G, "connections": cs})
    fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    if fails:
        LOG["errors"].append({"conns": fails})
    return len(fails)


# ═══ 0) 프리플라이트: 핵심 노드 존재 확인 ═══
sw = call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": G, "node_id": "K2Node_SwitchEnum_0"})
ledge_pin = [p for p in sw["pins"] if p["name"] == "SB_MOVE_Ledge"][0]
assert ledge_pin["connected_to"] == ["K2Node_ExecutionSequence_1.execute"], "Ledge 핀 배선 상이: %s" % ledge_pin["connected_to"]
seq0 = call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": G, "node_id": "K2Node_ExecutionSequence_0"})
t3 = [p for p in seq0["pins"] if p["name"] == "then_3"][0]
assert not t3["connected_to"], "then_3 이미 사용 중: %s" % t3["connected_to"]
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": BP}).get("variables", [])}
for req_v in ("LedgeHandIKAlphaL", "LedgeHandIKAlphaR", "LedgeFootIKAlphaL", "LedgeFootIKAlphaR",
              "LedgeDangleAlpha", "LedgePelvisSpring", "LedgeSlopeDzBody", "LedgePhysWanted", "LedgePhysProfileOn"):
    assert req_v in existing, "레이어 변수 없음: %s" % req_v
LOG["steps"].append("preflight ok")

# ═══ 1) 변수 ═══
if "LedgeCaseTick" not in existing:
    call("blueprint_query", "add_variable",
         {"asset_path": BP, "name": "LedgeCaseTick", "type": "bool", "default_value": "false",
          "category": "Custom Move|Ledge"})
LOG["steps"].append("var LedgeCaseTick")

# ═══ 2) Ledge 케이스 헤드 스플라이스 ═══
setTick = add("VariableSet", 1550, 1500, variable_name="LedgeCaseTick")
pindef(setTick, "LedgeCaseTick", "true")
call("blueprint_query", "disconnect_pins",
     {"asset_path": BP, "graph_name": G, "source_node": "K2Node_SwitchEnum_0", "source_pin": "SB_MOVE_Ledge",
      "target_node": "K2Node_ExecutionSequence_1", "target_pin": "execute"})
f = connect([
    {"source_node": "K2Node_SwitchEnum_0", "source_pin": "SB_MOVE_Ledge", "target_node": setTick, "target_pin": "execute"},
    {"source_node": setTick, "source_pin": "then", "target_node": "K2Node_ExecutionSequence_1", "target_pin": "execute"},
])
LOG["steps"].append("ledge head splice fail=%d setTick=%s" % (f, setTick))

# ═══ 3) then_3 리셋 체인 ═══
getTick = add("VariableGet", 700, 3000, variable_name="LedgeCaseTick")
brA = add("Branch", 900, 2900)
setTickF = add("VariableSet", 1150, 2820, variable_name="LedgeCaseTick")
pindef(setTickF, "LedgeCaseTick", "false")

zs = []
x = 1150
for nm, dv in [("LedgeHandIKAlphaL", "0.0"), ("LedgeHandIKAlphaR", "0.0"),
               ("LedgeFootIKAlphaL", "0.0"), ("LedgeFootIKAlphaR", "0.0"),
               ("LedgeDangleAlpha", "0.0"), ("LedgePelvisSpring", "0.0"),
               ("LedgeSlopeDzBody", "0.0"), ("LedgePhysWanted", "false")]:
    nid = add("VariableSet", x, 3050, variable_name=nm)
    pindef(nid, nm, dv)
    zs.append(nid)
    x += 230

getPOn = add("VariableGet", x, 3250, variable_name="LedgePhysProfileOn")
brC = add("Branch", x + 200, 3050)

cs = [
    {"source_node": "K2Node_ExecutionSequence_0", "source_pin": "then_3", "target_node": brA, "target_pin": "execute"},
    {"source_node": getTick, "source_pin": "LedgeCaseTick", "target_node": brA, "target_pin": "Condition"},
    {"source_node": brA, "source_pin": "then", "target_node": setTickF, "target_pin": "execute"},
    {"source_node": brA, "source_pin": "else", "target_node": zs[0], "target_pin": "execute"},
]
for a, b in zip(zs, zs[1:]):
    cs.append({"source_node": a, "source_pin": "then", "target_node": b, "target_pin": "execute"})
cs += [
    {"source_node": zs[-1], "source_pin": "then", "target_node": brC, "target_pin": "execute"},
    {"source_node": getPOn, "source_pin": "LedgePhysProfileOn", "target_node": brC, "target_pin": "Condition"},
    # 기존 Kinematic 오프 시퀀스 재사용 (Enable Kinematic -> Disable -> Set LedgePhysProfileOn<-LedgePhysWanted(이미 false))
    {"source_node": brC, "source_pin": "then", "target_node": "K2Node_CallFunction_18", "target_pin": "execute"},
]
f = connect(cs)
LOG["steps"].append("reset chain links fail=%d" % f)

# ═══ 4) 컴파일 ═══
cr = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
LOG["steps"].append("compile: %s" % json.dumps(cr, ensure_ascii=False)[:250])
