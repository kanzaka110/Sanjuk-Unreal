"""Export UpdateWallHandIK graph to disk = backup + offline analysis source.
Hits Monolith HTTP JSON-RPC directly so the 283-node dump never enters chat context.
Writes: backup_UpdateWallHandIK_<ts>.json  +  a terse edge/cluster summary .txt
"""
import json, urllib.request, datetime, collections, os

MCP = "http://localhost:9316/mcp"
BP  = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
G   = "UpdateWallHandIK"
HERE = os.path.dirname(os.path.abspath(__file__))

def call(action, params):
    body = {"jsonrpc":"2.0","id":1,"method":"tools/call",
            "params":{"name":"blueprint_query","arguments":{"action":action,"params":params}}}
    req = urllib.request.Request(MCP, data=json.dumps(body).encode(),
                                 headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = json.loads(r.read().decode())
    # unwrap MCP tool result
    if "result" in raw and "content" in raw["result"]:
        txt = raw["result"]["content"][0]["text"]
        return json.loads(txt)
    return raw

ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
data = call("export_graph", {"asset_path": BP, "graph_name": G})

bpath = os.path.join(HERE, f"backup_UpdateWallHandIK_{ts}.json")
with open(bpath, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)

nodes = data.get("nodes", [])
conns = data.get("connections", []) or data.get("edges", [])

# node id -> title/class
info = {}
for n in nodes:
    nid = n.get("id") or n.get("node_id")
    info[nid] = (n.get("class",""), n.get("title",""))

lines = []
lines.append(f"nodes={len(nodes)} connections={len(conns)}")
lines.append(f"top-level keys={list(data.keys())}")
# class histogram (non-knot)
hist = collections.Counter(c for c,_ in info.values())
lines.append("\n== class histogram ==")
for c,n in hist.most_common():
    lines.append(f"{n:4d}  {c}")
# title histogram for CallFunction
th = collections.Counter(t for c,t in info.values() if c=="K2Node_CallFunction")
lines.append("\n== CallFunction title histogram ==")
for t,n in th.most_common():
    lines.append(f"{n:4d}  {t}")

spath = os.path.join(HERE, f"summary_UpdateWallHandIK_{ts}.txt")
with open(spath, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("BACKUP:", bpath)
print("SUMMARY:", spath)
print("\n".join(lines[:40]))
