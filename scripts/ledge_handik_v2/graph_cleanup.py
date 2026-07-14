# Ledge 그래프 대청소 (로컬 HTTP) — v6 정리 라운드
# 1) 미사용 변수 Set 4개 exec 스플라이스 후 제거 (외부 리더 0 확인 선행)
# 2) 반복 도달성 분석으로 죽은 노드 전부 제거
# 3) GetWorldDeltaSeconds 중복 → 1개 통합
# 4) 미사용 변수 4개 삭제
import json, urllib.request, time

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
G = "Ledge"
LOG = []


def call(tool, action, params, timeout=180):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(txt[:300])
    return json.loads(txt)


def get_graph():
    return call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": G})


def analyze(g):
    nodes = {n["id"]: n for n in g["nodes"]}
    exec_live = set()
    roots = [nid for nid, n in nodes.items()
             if "FunctionEntry" in n.get("class", "") or "Event" in n.get("class", "")]
    stack = list(roots)
    while stack:
        nid = stack.pop()
        if nid in exec_live:
            continue
        exec_live.add(nid)
        for p in nodes[nid].get("pins", []):
            if p.get("type") == "exec" and p.get("direction") == "output":
                for c in p.get("connected_to", []):
                    peer = c.split(".")[0]
                    if peer in nodes:
                        stack.append(peer)
    live = set(exec_live)
    stack = list(exec_live)
    while stack:
        nid = stack.pop()
        for p in nodes[nid].get("pins", []):
            if p.get("type") != "exec" and p.get("direction") == "input":
                for c in p.get("connected_to", []):
                    peer = c.split(".")[0]
                    if peer in nodes and peer not in live:
                        live.add(peer)
                        stack.append(peer)
    comments = {nid for nid, n in nodes.items() if "Comment" in n.get("class", "")}
    dead = [nid for nid in nodes if nid not in live and nid not in comments]
    return nodes, live, dead


def remove_node(nid):
    try:
        call("blueprint_query", "remove_node", {"asset_path": ABP, "graph_name": G, "node_id": nid})
        LOG.append("removed " + nid)
        return True
    except Exception as e:
        LOG.append("REMOVE ERR %s: %r" % (nid, str(e)[:120]))
        return False


# ---- 0) 미사용 변수 외부 리더 확인
DEAD_VARS = ["LedgeHandGripGateL", "LedgeHandGripGateR", "LedgeHandDestL", "LedgeHandDestR"]
removable_vars = []
for v in DEAD_VARS:
    res = call("blueprint_query", "search_nodes", {"asset_path": ABP, "query": v})
    gets_outside = [x for x in res.get("results", [])
                    if x.get("class") == "K2Node_VariableGet" and x.get("graph") != G]
    if gets_outside:
        LOG.append("KEEP var %s — external readers: %s" % (v, gets_outside))
    else:
        removable_vars.append(v)
LOG.append("removable vars: %s" % removable_vars)

# ---- 1) 해당 변수의 Set 노드 exec 스플라이스 + 제거
g = get_graph()
nodes, live, dead = analyze(g)
for nid, n in list(nodes.items()):
    if n.get("class") != "K2Node_VariableSet":
        continue
    title = n.get("title", "")
    var = title.replace("Set ", "").strip()
    if var not in removable_vars:
        continue
    src = tgt = None
    for p in n.get("pins", []):
        if p.get("type") == "exec" and p.get("direction") == "input":
            for c in p.get("connected_to", []):
                src = c  # "Node.then"
        if p.get("type") == "exec" and p.get("direction") == "output":
            for c in p.get("connected_to", []):
                tgt = c  # "Node.execute"
    if src and tgt:
        sn, sp = src.rsplit(".", 1)
        tn, tp = tgt.rsplit(".", 1)
        try:
            call("blueprint_query", "connect_pins",
                 {"asset_path": ABP, "graph_name": G,
                  "source_node": sn, "source_pin": sp, "target_node": tn, "target_pin": tp})
            LOG.append("SPLICE %s: %s -> %s" % (nid, src, tgt))
        except Exception as e:
            LOG.append("SPLICE ERR %s: %r" % (nid, str(e)[:120]))
            continue
    remove_node(nid)

# ---- 2) 반복 죽은노드 제거 (연쇄 고아 소탕)
for it in range(6):
    g = get_graph()
    nodes, live, dead = analyze(g)
    if not dead:
        LOG.append("iter %d: no dead" % it)
        break
    LOG.append("iter %d: removing %d dead" % (it, len(dead)))
    for nid in dead:
        remove_node(nid)

# ---- 3) GetWorldDeltaSeconds 통합
g = get_graph()
nodes, live, dead = analyze(g)
gwds = [nid for nid, n in nodes.items() if n.get("function") == "GetWorldDeltaSeconds"]
if len(gwds) > 1:
    keeper = "K2Node_CallFunction_162" if "K2Node_CallFunction_162" in gwds else gwds[0]
    for nid in gwds:
        if nid == keeper:
            continue
        n = nodes[nid]
        consumers = []
        for p in n.get("pins", []):
            if p.get("name") == "ReturnValue":
                consumers = list(p.get("connected_to", []))
        ok = True
        for c in consumers:
            tn, tp = c.rsplit(".", 1)
            try:
                call("blueprint_query", "connect_pins",
                     {"asset_path": ABP, "graph_name": G,
                      "source_node": keeper, "source_pin": "ReturnValue",
                      "target_node": tn, "target_pin": tp})
                LOG.append("GWDS rewire %s -> %s" % (c, keeper))
            except Exception as e:
                LOG.append("GWDS REWIRE ERR %s: %r" % (c, str(e)[:120]))
                ok = False
        if ok:
            remove_node(nid)
    LOG.append("GWDS consolidated: %d -> 1 (keeper %s)" % (len(gwds), keeper))

# ---- 4) 미사용 변수 삭제
for v in removable_vars:
    try:
        call("blueprint_query", "remove_variable", {"asset_path": ABP, "name": v})
        LOG.append("removed var " + v)
    except Exception as e:
        LOG.append("VAR ERR %s: %r" % (v, str(e)[:120]))

# ---- 최종 상태
g = get_graph()
nodes, live, dead = analyze(g)
LOG.append("FINAL: total=%d live=%d dead=%d" % (len(nodes), len(live), len(dead)))
open(r"C:/Users/SHIFTUP/AppData/Local/Temp/claude/ledge_cleanup_log.json", "w",
     encoding="utf-8").write(json.dumps(LOG, indent=1, ensure_ascii=False))
print("CLEANUP DONE — total=%d dead=%d" % (len(nodes), len(dead)))
