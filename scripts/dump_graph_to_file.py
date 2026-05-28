"""Dump a graph via Monolith HTTP API and save raw text content to file.

Usage: python dump_graph_to_file.py <graph_name> <output_path>
"""
import sys
import json
import urllib.request

graph_name = sys.argv[1]
output_path = sys.argv[2]
asset = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "blueprint_query",
        "arguments": {
            "action": "get_graph_data",
            "params": {"asset_path": asset, "graph_name": graph_name},
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
# Re-pretty-print for readability
try:
    parsed = json.loads(text)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=1, ensure_ascii=False)
    print(f"Saved {len(parsed.get('nodes', []))} nodes to {output_path}")
except json.JSONDecodeError:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Saved raw text to {output_path}")
