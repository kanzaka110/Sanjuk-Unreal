# Ledge_HandTarget exec 순서 복구 (2026-07-22 저녁)
# 1) VS_29(Set LedgeDestTd) 맨앞 → 체인 끝(VS_18 뒤)으로 이동 — Td에지 복구
# 2) VS_6(Set LedgeUnitMoveVec) → VS_26(Set AnchorR) 직후로 복귀 — Phase1 규약
# knot 경유 대비: 직결 핀 기준으로 스플라이스. 컴파일까지만, 저장 안 함.
import json
import urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
HT = "Ledge_HandTarget"
LOG = {"steps": [], "fails": []}


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:300])
    return json.loads(txt)


def graph():
    g = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": HT})
    return {n["id"]: n for n in g["nodes"]}


def pin(nodes, nid, name, direction):
    for p in nodes[nid]["pins"]:
        if p["name"] == name and p.get("direction") == direction:
            return p.get("connected_to") or []
    return []


def exec_in_src(nodes, nid):
    # execute 입력에 연결된 소스 (node, pin)
    c = pin(nodes, nid, "execute", "input")
    if len(c) != 1:
        raise SystemExit("%s.execute 링크 예상 밖: %s" % (nid, c))
    return tuple(c[0].split(".", 1))


def then_dst(nodes, nid):
    c = pin(nodes, nid, "then", "output")
    if len(c) != 1:
        raise SystemExit("%s.then 링크 예상 밖: %s" % (nid, c))
    return tuple(c[0].split(".", 1))


def resolve_fwd(nodes, nid, pname):
    # knot 통과하며 다음 실노드 찾기
    cur, cpin = nid, pname
    while True:
        c = pin(nodes, cur, cpin, "output")
        if not c:
            return None
        peer, ppin = c[0].split(".", 1)
        if "Knot" in nodes.get(peer, {}).get("class", ""):
            outs = [p["name"] for p in nodes[peer]["pins"] if p.get("direction") == "output"]
            cur, cpin = peer, outs[0]
            continue
        return peer


nodes = graph()

# ── 사전 검증: 논리 순서가 진단 때와 동일한지 (knot 해소 기준) ──
expect = [
    ("K2Node_FunctionEntry_0", "then", "K2Node_VariableSet_29"),   # Entry → DestTd
    ("K2Node_VariableSet_29", "then", "K2Node_VariableSet_28"),    # DestTd → Relatch
    ("K2Node_VariableSet_32", "then", "K2Node_VariableSet_6"),     # MoveOffset → UnitMoveVec
    ("K2Node_VariableSet_6", "then", "K2Node_VariableSet_33"),     # UnitMoveVec → PreOffset
    ("K2Node_VariableSet_26", "then", "K2Node_VariableSet_30"),    # AnchorR → McBaseL
]
for src, pname, want in expect:
    got = resolve_fwd(nodes, src, pname)
    if got != want:
        raise SystemExit("사전검증 실패 %s.%s → %s (기대 %s) — 중단" % (src, pname, got, want))
# VS_18.then 은 댕글링이어야 함
if pin(nodes, "K2Node_VariableSet_18", "then", "output"):
    raise SystemExit("VS_18.then 이 이미 연결됨 — 중단")
LOG["steps"].append("pre-verify OK")


def disconnect(nid, pname):
    call("blueprint_query", "disconnect_pins",
         {"asset_path": ABP, "graph_name": HT, "node_id": nid, "pin_name": pname})


def connect(conns):
    rc = call("blueprint_query", "connect_pins_bulk",
              {"asset_path": ABP, "graph_name": HT, "connections": conns})
    fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
    LOG["fails"] += fails
    if fails:
        raise SystemExit("connect 실패: " + json.dumps(fails, ensure_ascii=False)[:400])


# ── 1. VS_6 이동: (P → VS_6 → S) 절제 후 P→S 봉합, VS_26 뒤 삽입 ──
p_node, p_pin = exec_in_src(nodes, "K2Node_VariableSet_6")
s_node, s_pin = then_dst(nodes, "K2Node_VariableSet_6")
q_node, q_pin = then_dst(nodes, "K2Node_VariableSet_26")   # AnchorR의 기존 후속(직결, knot 가능)
disconnect(p_node, p_pin)
disconnect("K2Node_VariableSet_6", "then")
disconnect("K2Node_VariableSet_26", "then")
connect([
    {"source_node": p_node, "source_pin": p_pin, "target_node": s_node, "target_pin": s_pin},
    {"source_node": "K2Node_VariableSet_26", "source_pin": "then",
     "target_node": "K2Node_VariableSet_6", "target_pin": "execute"},
    {"source_node": "K2Node_VariableSet_6", "source_pin": "then",
     "target_node": q_node, "target_pin": q_pin},
])
LOG["steps"].append("VS_6 moved: %s.%s→%s.%s healed; VS_26→VS_6→%s" % (p_node, p_pin, s_node, s_pin, q_node))

# ── 2. VS_29 이동: 맨앞 절제 후 Entry→후속 봉합, 체인 끝(VS_18 뒤) 배치 ──
nodes = graph()  # 1번 변경 반영 재덤프
p2_node, p2_pin = exec_in_src(nodes, "K2Node_VariableSet_29")
s2_node, s2_pin = then_dst(nodes, "K2Node_VariableSet_29")
disconnect(p2_node, p2_pin)
disconnect("K2Node_VariableSet_29", "then")
connect([
    {"source_node": p2_node, "source_pin": p2_pin, "target_node": s2_node, "target_pin": s2_pin},
    {"source_node": "K2Node_VariableSet_18", "source_pin": "then",
     "target_node": "K2Node_VariableSet_29", "target_pin": "execute"},
])
LOG["steps"].append("VS_29 moved to tail: %s.%s→%s.%s healed; VS_18→VS_29(END)" % (p2_node, p2_pin, s2_node, s2_pin))

# ── 3. 컴파일 + 최종 순서 검증 ──
cp = call("blueprint_query", "compile", {"asset_path": ABP})
LOG["steps"].append("compile: " + json.dumps(cp, ensure_ascii=False)[:200])

nodes = graph()
order = []
cur = "K2Node_FunctionEntry_0"
guard = 0
while cur and guard < 60:
    guard += 1
    if "Knot" not in nodes[cur].get("class", "") and "FunctionEntry" not in nodes[cur].get("class", ""):
        order.append(cur)
    nxt = None
    for p in nodes[cur]["pins"]:
        if p.get("direction") == "output" and (p.get("type") == "exec" or "Knot" in nodes[cur].get("class", "")):
            c = p.get("connected_to") or []
            if c:
                nxt = c[0].split(".")[0]
                break
    cur = nxt
LOG["final_order"] = order
ok_tail = order[-1] == "K2Node_VariableSet_29"
i26 = order.index("K2Node_VariableSet_26")
ok_vs6 = order[i26 + 1] == "K2Node_VariableSet_6"
print("FIX_DONE tail_ok=%s vs6_after_anchor_ok=%s" % (ok_tail, ok_vs6))
for s in LOG["steps"]:
    print("  " + s)
print("order:", " > ".join(o.replace("K2Node_VariableSet_", "VS_") for o in order))
json.dump(LOG, open(__file__.replace("fix_exec_order.py", "fix_exec_order_log.json"), "w",
                    encoding="utf-8"), indent=1, ensure_ascii=False)
