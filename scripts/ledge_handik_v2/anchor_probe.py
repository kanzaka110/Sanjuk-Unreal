# 앵커 주입(재래치 소스 +DzHold) 배선 추적 (2026-07-25)
# Ledge_HandTarget에서 LedgeSlopeDzHoldL/R getter → 소비 체인(MakeVector/Add/Select/래치)을 역추적 덤프
import json
import urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
G = "Ledge_HandTarget"


def call(tool: str, action: str, params: dict, timeout: int = 300) -> dict:
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:400])
    return json.loads(txt)


def bq(action: str, params: dict) -> dict:
    p = {"asset_path": ABP}
    p.update(params)
    return call("blueprint_query", action, p)


nodes = {n["id"]: n for n in bq("get_graph_data", {"graph_name": G})["nodes"]}
print("[HT] nodes:", len(nodes))


def pin_map(nid: str) -> dict:
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


def show(nid: str, depth: int) -> None:
    pm = pin_map(nid)
    tags = []
    for pname, p in pm.items():
        dv = p.get("default_value")
        if dv not in (None, "") and p.get("direction") == "input":
            tags.append(f"{pname}={dv}")
    print("  " * depth + f"{nid} | {' '.join(tags)}")
    for pname, p in pm.items():
        for c in p.get("connected_to", []) or []:
            print("  " * depth + f"    {pname}->{c}")


# DzHold getter 찾기
seeds = []
for nid, n in nodes.items():
    for p in n.get("pins", []):
        if p["name"] in ("LedgeSlopeDzHoldL", "LedgeSlopeDzHoldR") and p.get("direction") == "output":
            seeds.append((nid, p["name"], p.get("connected_to", []) or []))

visited = set()
for nid, pname, conns in seeds:
    print(f"\n[SEED] {nid}.{pname} -> {conns}")
    frontier = [c.split(".")[0] for c in conns]
    depth = 1
    while frontier and depth <= 4:
        nxt = []
        for f in frontier:
            if f in visited or f not in nodes:
                continue
            visited.add(f)
            show(f, depth)
            for p in nodes[f].get("pins", []):
                if p.get("direction") == "output":
                    for c in p.get("connected_to", []) or []:
                        nxt.append(c.split(".")[0])
        frontier = nxt
        depth += 1
