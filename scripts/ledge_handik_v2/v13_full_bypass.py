# v13 전체 우회(오늘 낮 상태 재현) — 노드 삭제 없이 exec 직결만. 재적용 = reapply 스크립트.
# A. OnStateEntry_EventTransit: Entry->VS_0 직결(가드 우회) + CF.then->Result(setT 우회) + bForceBlend 절단(디폴트 false)
# B. UpdateStates: VS_19.then->VS_20 직결(setPrevTr 우회)
# C. IsStateMachineBlendStackAnimInBlendOut: LessEqual.B 절단(디폴트 0.5 복원)
# D. SetStateMachineBlendStackAnim: Entry->Sequence 직결(setF 우회)
# E. OnStateEntry_EventMove: CF.then->Result 직결(setT 우회)
# ⚠ 로컬 python 전용.
import json, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
LOG = []


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


def graph(g):
    return {n["id"]: n for n in call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": g})["nodes"]}


def pins(n):
    return {p["name"]: p for p in n.get("pins", [])}


def conn(ns, nid, pin):
    return (pins(ns[nid]).get(pin, {}).get("connected_to") or [])


def relink(g, src, spin, dst, dpin):
    call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": g, "node_id": src, "pin_name": spin})
    call("blueprint_query", "connect_pins", {"asset_path": ABP, "graph_name": g,
                                             "source_node": src, "source_pin": spin, "target_node": dst, "target_pin": dpin})


# ── A ──
G = "OnStateEntry_EventTransit"
ns = graph(G)
ent = [i for i, n in ns.items() if n["class"] == "K2Node_FunctionEntry"][0]
vs0 = [i for i, n in ns.items() if n["class"] == "K2Node_VariableSet" and "TargetRotationDelta" in n.get("title", "")][0]
cf = [i for i, n in ns.items() if n.get("function") == "SetStateMachineBlendStackAnim"][0]
res = [i for i, n in ns.items() if n["class"] == "K2Node_FunctionResult"][0]
relink(G, ent, "then", vs0, "execute")
relink(G, cf, "then", res, "execute")
if conn(ns, cf, "bForceBlend"):
    call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": G, "node_id": cf, "pin_name": "bForceBlend"})
LOG.append("A: guard/setT/forceBlend 우회")

# ── B ──
G = "UpdateStates"
ns = graph(G)
vs19 = vs20 = None
for i, n in ns.items():
    t = n.get("title", "")
    if n["class"] == "K2Node_VariableSet":
        if "bTransitMoving" in t and "Prev" not in t:
            vs19 = i
        elif "TransitingToNextLedge" in t and "Prev" not in t:
            vs20 = i
relink(G, vs19, "then", vs20, "execute")
LOG.append("B: prevTr 우회")

# ── C ──
G = "IsStateMachineBlendStackAnimInBlendOut"
ns = graph(G)
le = [i for i, n in ns.items() if n["class"] == "K2Node_PromotableOperator"][0]
if conn(ns, le, "B"):
    call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": G, "node_id": le, "pin_name": "B"})
call("blueprint_query", "set_pin_default", {"asset_path": ABP, "graph_name": G, "node_id": le, "pin_name": "B", "value": "0.5"})
LOG.append("C: 문턱 0.5 복원")

# ── D ──
G = "SetStateMachineBlendStackAnim"
relink(G, "K2Node_FunctionEntry_0", "then", "K2Node_ExecutionSequence_0", "execute")
LOG.append("D: setF 우회")

# ── E ──
G = "OnStateEntry_EventMove"
ns = graph(G)
cf = [i for i, n in ns.items() if n.get("function") == "SetStateMachineBlendStackAnim"][0]
res = [i for i, n in ns.items() if n["class"] == "K2Node_FunctionResult"][0]
relink(G, cf, "then", res, "execute")
LOG.append("E: EventMove setT 우회")

# ── 검증 ──
checks = []
ns = graph("OnStateEntry_EventTransit")
ent = [i for i, n in ns.items() if n["class"] == "K2Node_FunctionEntry"][0]
checks.append(("A entry", "TargetRotationDelta" in ns[conn(ns, ent, "then")[0].split(".")[0]].get("title", "") if conn(ns, ent, "then") else False))
cf = [i for i, n in ns.items() if n.get("function") == "SetStateMachineBlendStackAnim"][0]
checks.append(("A cf->result", "FunctionResult" in str(conn(ns, cf, "then"))))
checks.append(("A forceblend cut", not conn(ns, cf, "bForceBlend")))
ns = graph("UpdateStates")
vs19 = [i for i, n in ns.items() if n["class"] == "K2Node_VariableSet" and "bTransitMoving" in n.get("title", "") and "Prev" not in n.get("title", "")][0]
checks.append(("B", "TransitingToNextLedge" in ns[conn(ns, vs19, "then")[0].split(".")[0]].get("title", "")))
ns = graph("IsStateMachineBlendStackAnimInBlendOut")
le = [i for i, n in ns.items() if n["class"] == "K2Node_PromotableOperator"][0]
checks.append(("C", not conn(ns, le, "B") and pins(ns[le])["B"].get("default_value") in ("0.5", "0.500000")))
ns = graph("SetStateMachineBlendStackAnim")
checks.append(("D", "K2Node_ExecutionSequence_0" in str(conn(ns, "K2Node_FunctionEntry_0", "then"))))
ns = graph("OnStateEntry_EventMove")
cf = [i for i, n in ns.items() if n.get("function") == "SetStateMachineBlendStackAnim"][0]
checks.append(("E", "FunctionResult" in str(conn(ns, cf, "then"))))
bad = [c for c, ok in checks if not ok]
print("BYPASS:", " / ".join(LOG))
print("VERIFY:", "ALL OK" if not bad else "FAIL: %s" % bad)
if bad:
    raise SystemExit(1)
