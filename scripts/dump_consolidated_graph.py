#!/usr/bin/env python3
"""Dump AnimRewindRecorderEmit graph to JSON + count nodes."""
from __future__ import annotations

import json
import urllib.request

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "AnimRewindRecorderEmit"
ENDPOINT = "http://localhost:9316/mcp"
OUT = r"C:\Dev\Sanjuk-Unreal\Saved\PROBE_AnimRewindRecorderEmit_consolidated_20260514.json"


def rpc(action: str, params: dict) -> dict | None:
    body = {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "blueprint_query", "arguments": {"action": action, "params": params}},
    }
    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if data.get("result", {}).get("isError"):
        print("ERROR:", data["result"]["content"][0]["text"][:600])
        return None
    return json.loads(data["result"]["content"][0]["text"])


def main() -> None:
    info = rpc("get_graph_data", {"asset_path": ASSET, "graph_name": GRAPH})
    if info is None:
        return
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    nodes = info.get("nodes", [])
    print(f"Saved {OUT}")
    print(f"Total nodes: {len(nodes)}")
    fts = [n for n in nodes if n.get("class") == "K2Node_FormatText"]
    print(f"FormatText nodes: {len(fts)}")
    for n in fts:
        print(f"  - {n['id']}")


if __name__ == "__main__":
    main()
