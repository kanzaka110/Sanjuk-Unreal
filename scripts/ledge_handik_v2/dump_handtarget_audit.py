# Ledge_HandTarget 그래프 덤프 + 정리 후유증 진단 (read-only)
import json
import urllib.request
import os

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
HT = "Ledge_HandTarget"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


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


g = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": HT})
with open(os.path.join(OUT_DIR, "handtarget_dump.json"), "w", encoding="utf-8") as f:
    json.dump(g, f, ensure_ascii=False)

nodes = {n["id"]: n for n in g["nodes"]}
report = {"node_count": len(nodes)}


def title(nid):
    return str(nodes.get(nid, {}).get("title", "?")).split(chr(10))[0]


# 1) 끊긴 링크: connected_to 가 존재하지 않는 노드를 가리키는 핀
broken = []
for nid, n in nodes.items():
    for p in n.get("pins", []):
        for c in p.get("connected_to") or []:
            peer = c.split(".")[0]
            if peer not in nodes:
                broken.append({"node": nid, "title": title(nid), "pin": p["name"],
                               "dir": p.get("direction"), "missing_peer": c})
report["broken_links"] = broken

# 2) exec 도달성 (knot 무조건 통과 — pitfalls #7)
roots = [nid for nid, n in nodes.items()
         if "FunctionEntry" in n.get("class", "") or "Event" in n.get("class", "")]
exec_live = set()
stack = list(roots)
while stack:
    nid = stack.pop()
    if nid in exec_live:
        continue
    exec_live.add(nid)
    for p in nodes[nid].get("pins", []):
        is_exec = p.get("type") == "exec" or "Knot" in nodes[nid].get("class", "")
        if is_exec and p.get("direction") == "output":
            for c in p.get("connected_to") or []:
                peer = c.split(".")[0]
                if peer in nodes:
                    stack.append(peer)
live = set(exec_live)
stack = list(exec_live)
while stack:
    nid = stack.pop()
    for p in nodes[nid].get("pins", []):
        if p.get("type") != "exec" and p.get("direction") == "input":
            for c in p.get("connected_to") or []:
                peer = c.split(".")[0]
                if peer in nodes and peer not in live:
                    live.add(peer)
                    stack.append(peer)
comments = {nid for nid, n in nodes.items() if "Comment" in n.get("class", "")}
dead = sorted(nid for nid in nodes if nid not in live and nid not in comments)
report["roots"] = [(r, title(r)) for r in roots]
report["dead_nodes"] = [(d, title(d)) for d in dead]

# 3) exec 출력이 아무데도 안 이어지는 노드 (체인 단절 의심)
exec_dangling = []
for nid, n in nodes.items():
    if nid not in exec_live:
        continue
    for p in n.get("pins", []):
        if p.get("type") == "exec" and p.get("direction") == "output":
            if not (p.get("connected_to") or []) and "Result" not in n.get("class", ""):
                exec_dangling.append({"node": nid, "title": title(nid), "pin": p["name"]})
report["exec_dangling"] = exec_dangling

# 4) 변수 Get/Set 이 참조하는 변수명 수집 (삭제된 변수 참조 탐지용)
var_refs = {}
for nid, n in nodes.items():
    cls = n.get("class", "")
    if "VariableGet" in cls or "VariableSet" in cls:
        vn = n.get("member_name") or n.get("variable_name") or title(nid)
        var_refs.setdefault(str(vn), []).append(nid)
report["var_refs"] = {k: v for k, v in sorted(var_refs.items())}

# 5) 핵심 노드 확인: Lerp206/207, CF_20/21(Subtract), CF_96, CF_168/169, VInterp, Select
keys = {}
for probe in ["CallFunction_206", "CallFunction_207", "CallFunction_20", "CallFunction_21",
              "CallFunction_96", "CallFunction_168", "CallFunction_169", "CallFunction_0"]:
    n = nodes.get("K2Node_" + probe)
    if n is None:
        keys[probe] = "MISSING"
    else:
        pins = {}
        for p in n.get("pins", []):
            if p.get("direction") == "input" and p.get("type") != "exec":
                pins[p["name"]] = {"src": p.get("connected_to") or [],
                                   "default": p.get("default_value")}
        keys[probe] = {"title": title("K2Node_" + probe), "inputs": pins}
report["key_nodes"] = keys

# 6) 살아있는 노드 중 입력 데이터 핀이 미연결+디폴트 없음 (의심 핀)
suspect = []
for nid in sorted(live):
    n = nodes[nid]
    cls = n.get("class", "")
    if "Comment" in cls or "Knot" in cls:
        continue
    for p in n.get("pins", []):
        if (p.get("direction") == "input" and p.get("type") not in ("exec", None)
                and not (p.get("connected_to") or [])):
            dv = p.get("default_value")
            if dv in (None, "", "None"):
                suspect.append({"node": nid, "title": title(nid), "pin": p["name"],
                                "pin_type": p.get("type")})
report["unconnected_inputs"] = suspect

with open(os.path.join(OUT_DIR, "handtarget_audit.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)

print("nodes:", report["node_count"])
print("broken_links:", len(broken))
for b in broken[:20]:
    print("  BR", b["node"], b["pin"], "->", b["missing_peer"])
print("dead_nodes:", len(dead))
for d, t in report["dead_nodes"][:30]:
    print("  DEAD", d, t)
print("exec_dangling:", len(exec_dangling))
for e in exec_dangling[:15]:
    print("  EXEC-END", e["node"], e["title"], e["pin"])
print("key_nodes:")
for k, v in keys.items():
    if v == "MISSING":
        print("  KEY", k, "MISSING")
    else:
        print("  KEY", k, v["title"])
print("unconnected_inputs:", len(suspect))
