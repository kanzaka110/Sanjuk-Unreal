# ABP 렛지 그래프 대청소 — 1단계: 스캔 (read-only)
# 도달성(픽폴 반영: knot IO=입력취급, 서브핀, exec/데이터 구분) + 미사용 변수 + 특수 패턴(K=0 lead 등)
import json, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
OUT = r"C:/Users/SHIFTUP/AppData/Local/Temp/claude/cleanup_scan.json"
GRAPHS = ["Ledge", "Ledge_CalcVelocity", "Ledge_DangleAlpha", "Ledge_HandAlpha",
          "Ledge_HandTarget", "Ledge_FootTarget", "Ledge_FootGate", "LedgeDebugs", "LedgeState",
          "Ledge_SlopeZ", "Ledge_LineSnap", "Ledge_ProcWindow", "EventGraph", "AnimGraph"]


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


report = {"graphs": {}, "raw": {}}

for G in GRAPHS:
    try:
        g = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": G})
    except RuntimeError as e:
        report["graphs"][G] = {"error": str(e)[:120]}
        continue
    nodes = {n["id"]: n for n in g.get("nodes", [])}
    report["raw"][G] = g  # 백업 겸용

    def pins(n):
        return n.get("pins", [])

    # 1) exec 도달: 엔트리/이벤트에서 exec 출력 따라가기 (knot: exec형 IO 핀도 따름)
    roots = [nid for nid, n in nodes.items()
             if "FunctionEntry" in n.get("class", "") or n.get("class", "").startswith("K2Node_Event")
             or "InputAction" in n.get("class", "")]
    exec_live = set()
    stack = list(roots)
    while stack:
        nid = stack.pop()
        if nid in exec_live:
            continue
        exec_live.add(nid)
        n = nodes.get(nid)
        if not n:
            continue
        for p in pins(n):
            if p.get("is_exec") or p.get("type") == "exec":
                if p.get("direction") == "output" or "Knot" in n.get("class", ""):
                    for c in p.get("connected_to", []):
                        peer = c.split(".")[0]
                        if peer in nodes:
                            stack.append(peer)

    # 2) 데이터 폐포: live 노드의 모든 입력(+knot은 전 핀) 소스 추가. 서브핀 포함(핀 리스트에 나오는 전부)
    live = set(exec_live)
    stack = list(exec_live)
    while stack:
        nid = stack.pop()
        n = nodes.get(nid)
        if not n:
            continue
        is_knot = "Knot" in n.get("class", "")
        for p in pins(n):
            is_exec = p.get("is_exec") or p.get("type") == "exec"
            if is_exec:
                continue
            if p.get("direction") == "input" or is_knot:
                for c in p.get("connected_to", []):
                    peer = c.split(".")[0]
                    if peer in nodes and peer not in live:
                        live.add(peer)
                        stack.append(peer)

    comments = {nid for nid, n in nodes.items() if "Comment" in n.get("class", "")}
    dead = [nid for nid in nodes if nid not in live and nid not in comments]
    # dead 상세 + 안전 재확인: dead 노드의 출력이 live 노드로 연결돼 있으면 오탐 (제외)
    false_pos = []
    for nid in list(dead):
        n = nodes[nid]
        for p in pins(n):
            if p.get("direction") == "output":
                for c in p.get("connected_to", []):
                    if c.split(".")[0] in live:
                        false_pos.append(nid)
                        break
    dead = [d for d in dead if d not in false_pos]

    # 특수 패턴: PrintString 노드 (exec 미연결)
    prints = [nid for nid, n in nodes.items() if n.get("function") == "PrintString"]

    report["graphs"][G] = {
        "total": len(nodes), "live": len(live), "dead_count": len(dead),
        "false_pos_excluded": false_pos,
        "dead": [{"id": nid, "class": nodes[nid].get("class", ""), "fn": nodes[nid].get("function", ""),
                  "title": (nodes[nid].get("title") or "").split(chr(10))[0]} for nid in sorted(dead)],
        "print_nodes": prints,
    }

# 3) 변수: Ledge* 변수 참조 수
vres = call("blueprint_query", "get_variables", {"asset_path": ABP})
ledge_vars = [v["name"] for v in vres.get("variables", []) if v["name"].startswith("Ledge")]
var_refs = {}
for vn in ledge_vars:
    try:
        r = call("blueprint_query", "find_variable_references", {"asset_path": ABP, "variable_name": vn})
        cnt = r.get("reference_count", r.get("count", len(r.get("references", []))))
        var_refs[vn] = cnt
    except RuntimeError as e:
        var_refs[vn] = "ERR " + str(e)[:60]
report["ledge_var_refs"] = var_refs
report["unused_vars"] = [v for v, c in var_refs.items() if c == 0]

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=1, ensure_ascii=False)

for G in GRAPHS:
    gr = report["graphs"].get(G, {})
    if "error" in gr:
        print(G, "ERR", gr["error"])
    else:
        print(f"{G}: total={gr['total']} live={gr['live']} dead={gr['dead_count']} print={len(gr['print_nodes'])}")
print("미사용 Ledge 변수:", report["unused_vars"])
print("-> " + OUT)
