# Ledge 함수 그래프 도달성 분석 (로컬 실행, Monolith HTTP)
# live = exec 체인 + 데이터 입력 폐포. dead = 나머지 (Comment 제외)
import json, urllib.request, collections

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
OUT = r"C:/Users/SHIFTUP/AppData/Local/Temp/claude/ledge_graph_analysis.json"
RAW = r"C:/Users/SHIFTUP/AppData/Local/Temp/claude/ledge_graph_raw.json"


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


g = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": "Ledge"})
open(RAW, "w", encoding="utf-8").write(json.dumps(g, indent=1))

nodes = {}
for n in g.get("nodes", []):
    nodes[n["id"]] = n

# 링크 인덱스: (node, pin_name) -> [(peer_node, peer_pin, dir, is_exec)]
def pins(n):
    return n.get("pins", [])

exec_live = set()
# 진입점: FunctionEntry / 이벤트류
roots = [nid for nid, n in nodes.items()
         if "FunctionEntry" in n.get("class", "") or "Event" in n.get("class", "")]
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
        if (p.get("type")=="exec") and p.get("direction") == "output":
            for c in p.get("connected_to", []):
                peer = c.split(".")[0]
                if peer in nodes:
                    stack.append(peer)

# 데이터 폐포: live 노드의 입력 데이터 핀 소스를 재귀 추가
live = set(exec_live)
stack = list(exec_live)
while stack:
    nid = stack.pop()
    n = nodes.get(nid)
    if not n:
        continue
    for p in pins(n):
        if not (p.get("type")=="exec") and p.get("direction") == "input":
            for c in p.get("connected_to", []):
                peer = c.split(".")[0]
                if peer in nodes and peer not in live:
                    live.add(peer)
                    stack.append(peer)

comments = {nid for nid, n in nodes.items() if "Comment" in n.get("class", "")}
dead = [nid for nid in nodes if nid not in live and nid not in comments]

result = {
    "total": len(nodes),
    "live": len(live),
    "comments": len(comments),
    "dead_count": len(dead),
    "dead": [{"id": nid, "class": nodes[nid].get("class", ""),
              "title": (nodes[nid].get("title") or "").split(chr(10))[0]} for nid in sorted(dead)],
    "exec_roots": roots,
}
# GetWorldDeltaSeconds 중복 카운트 (live 안)
gwds = [nid for nid in live if nodes[nid].get("function") == "GetWorldDeltaSeconds"]
result["gwds_live"] = gwds
open(OUT, "w", encoding="utf-8").write(json.dumps(result, indent=1, ensure_ascii=False))
print("total=%d live=%d dead=%d comments=%d" % (len(nodes), len(live), len(dead), len(comments)))
