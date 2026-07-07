"""Delete the 7 swimlane comment boxes I added to UpdateWallHandIK (find via circled numbers)."""
import json, urllib.request
MCP="http://localhost:9316/mcp"; BP="/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"; G="UpdateWallHandIK"
def call(a,p):
    b={"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"blueprint_query","arguments":{"action":a,"params":p}}}
    r=urllib.request.Request(MCP,data=json.dumps(b).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=120) as x: raw=json.loads(x.read().decode())
    if "result" in raw and "content" in raw["result"]: return json.loads(raw["result"]["content"][0]["text"])
    return raw
ids=set()
for mark in ['①','②','③','④','⑤','⑥','⑦']:
    r=call("search_nodes",{"asset_path":BP,"query":mark})
    for res in r.get('results',[]):
        if res.get('graph')=='UpdateWallHandIK' and res.get('class')=='EdGraphNode_Comment':
            ids.add(res['node_id']);
print("swimlane comment ids:",sorted(ids))
for cid in sorted(ids):
    r=call("remove_node",{"asset_path":BP,"graph_name":G,"node_id":cid})
    print(f"  del {cid}: {r.get('success')}")
print("compile:", call("compile_blueprint",{"asset_path":BP}).get('success'))
