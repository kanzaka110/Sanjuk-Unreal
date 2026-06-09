"""Dump PC_01_CtrlRig_FootClamp 'Rig' graph via Monolith HTTP API to file.

Usage: python dump_footclamp_graph.py <output_path>
"""
import sys
import json
import urllib.request

output_path = sys.argv[1] if len(sys.argv) > 1 else "_sjleg/footclamp_rig_graph.json"
asset = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_FootClamp"

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "blueprint_query",
        "arguments": {
            "action": "get_graph_data",
            "params": {"asset_path": asset, "graph_name": "Rig"},
        },
    },
}

req = urllib.request.Request(
    "http://localhost:9316/mcp",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
)

with urllib.request.urlopen(req, timeout=120) as resp:
    body = json.loads(resp.read().decode())

text = body["result"]["content"][0]["text"]
try:
    parsed = json.loads(text)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=1, ensure_ascii=False)
    print(f"Saved {len(parsed.get('nodes', []))} nodes to {output_path}")
except json.JSONDecodeError:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Saved raw text ({len(text)} chars) to {output_path}")
