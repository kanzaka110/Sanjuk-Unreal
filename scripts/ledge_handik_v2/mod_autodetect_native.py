# AutoDetectCurves 를 네이티브로 재구성 — DetectWindow ×4 호출, 파이썬 노드 제거
#  손: Ratio 0.18 / Pad(-0.067, 0.033)   발: Ratio 0.32 / Pad(-0.017, 0.033)
#  ⚠ 노브를 바꾸면 derive_windows2.py(일괄용)와 같이 맞출 것
# ⚠ 로컬 python 전용
import json, urllib.request

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/TA/AnimModifiers/AM_SBLedgeIK"
G = "AutoDetectCurves"
LIMBS = [("hand_l", "HandMoveStartL", "HandMoveEndL", "0.18", "-0.067", "0.033", 0),
         ("hand_r", "HandMoveStartR", "HandMoveEndR", "0.18", "-0.067", "0.033", 400),
         ("ball_l", "FootMoveStartL", "FootMoveEndL", "0.32", "-0.017", "0.033", 800),
         ("ball_r", "FootMoveStartR", "FootMoveEndR", "0.32", "-0.017", "0.033", 1200)]


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:250])
    return json.loads(txt)


# 시그니처: Seq 입력 (OnApply 의 AnimationSequence 를 넘긴다)
call("blueprint_query", "set_function_params", {"asset_path": BP, "function_name": G,
     "inputs": [{"name": "Seq", "type": "object:AnimSequence"}]})

ns = {n["id"]: n for n in call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": G})["nodes"]}
entry = [i for i, n in ns.items() if "FunctionEntry" in n["class"]][0]
# 구 파이썬/플래그 노드 제거
for i, n in list(ns.items()):
    t = n.get("title", "").replace("\n", " ")
    if "Execute Python Command" in t or "bAutoDetectRequest" in t:
        try:
            call("blueprint_query", "remove_node", {"asset_path": BP, "graph_name": G, "node_id": i})
            print("removed", i, t[:40])
        except RuntimeError as e:
            print("rm fail", i, str(e)[:80])

nodes, defaults, data = [], [], []


def N(t, nt, x, y, **kw):
    d = {"temp_id": t, "node_type": nt, "position": [x, y]}
    d.update(kw)
    nodes.append(d)


def C(sn, sp, tn, tp):
    data.append({"source_node": sn, "source_pin": sp, "target_node": tn, "target_pin": tp})


def D(n, p, v):
    defaults.append({"node_id": n, "pin_name": p, "value": v})


for bone, ps, pe, ratio, pad0, pad1, y in LIMBS:
    k = bone.replace("_", "")
    N("call" + k, "CallFunction", 0, y, function_name="DetectWindow")
    C(entry, "Seq", "call" + k, "Seq")
    D("call" + k, "BoneName", bone)
    D("call" + k, "Ratio", ratio)
    D("call" + k, "PadStart", pad0)
    D("call" + k, "PadEnd", pad1)
    N("set" + k + "S", "VariableSet", 300, y, variable_name=ps)
    C("call" + k, "OutStart", "set" + k + "S", ps)
    N("set" + k + "E", "VariableSet", 520, y, variable_name=pe)
    C("call" + k, "OutEnd", "set" + k + "E", pe)

tm = {}


def harvest(o):
    if isinstance(o, dict):
        if o.get("temp_id") and (o.get("node_id") or o.get("id")):
            tm[o["temp_id"]] = o.get("node_id") or o.get("id")
        else:
            for v in o.values():
                harvest(v)
    elif isinstance(o, list):
        for e in o:
            harvest(e)


harvest(call("blueprint_query", "add_nodes_bulk", {"asset_path": BP, "graph_name": G, "nodes": nodes}))
missing = [n["temp_id"] for n in nodes if n["temp_id"] not in tm]
if missing:
    raise SystemExit("노드 생성 실패: %s" % missing)
for d in defaults:
    d["node_id"] = tm[d["node_id"]]
rd = call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": BP, "graph_name": G, "defaults": defaults})
print("default fails:", [x for x in (rd.get("results") or []) if not x.get("success", True)] or 0)
for c in data:
    c["source_node"] = tm.get(c["source_node"], c["source_node"])
    c["target_node"] = tm.get(c["target_node"], c["target_node"])

ex = []


def E(a, ap, b):
    ex.append({"source_node": tm.get(a, a), "source_pin": ap, "target_node": tm.get(b, b), "target_pin": "execute"})


prev, prevpin = entry, "then"
for bone, _, _, _, _, _, _ in LIMBS:
    k = bone.replace("_", "")
    E(prev, prevpin, "call" + k)
    E("call" + k, "then", "set" + k + "S")
    E("set" + k + "S", "then", "set" + k + "E")
    prev, prevpin = "set" + k + "E", "then"

rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": G, "connections": data + ex})
print("bulk fails:", [x for x in (rc.get("results") or []) if not x.get("success", True)][:5] or 0)
ns2 = {n["id"]: n for n in call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": G})["nodes"]}


def has(a, ap, b):
    for p in ns2.get(a, {}).get("pins", []):
        if p["name"] == ap:
            return any(x.split(".")[0] == b for x in (p.get("connected_to") or []))
    return False


miss = [(c["source_node"], c["source_pin"], c["target_node"]) for c in data + ex
        if not has(c["source_node"], c["source_pin"], c["target_node"])]
print("silent-drop:", miss if miss else "none")
r = call("blueprint_query", "compile_blueprint", {"asset_path": BP})
print("compile:", r.get("success"), "errors:", r.get("error_count"), (r.get("errors") or [])[:3])
