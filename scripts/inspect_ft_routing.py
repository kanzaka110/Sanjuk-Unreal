#!/usr/bin/env python3
"""Inspect FT_1 and new FT_2 connections to verify routing after STEP 4."""
from __future__ import annotations

import json
import urllib.request

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "AnimRewindRecorderEmit"
ENDPOINT = "http://localhost:9316/mcp"


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


for nid in ("K2Node_FormatText_1", "K2Node_FormatText_2", "K2Node_CallFunction_4", "K2Node_VariableSet_1"):
    info = rpc("get_node_details", {"asset_path": ASSET, "graph_name": GRAPH, "node_id": nid})
    if not info:
        print(f"--- {nid}: not found ---")
        continue
    print(f"\n=== {nid} ({info.get('class')}) ===")
    for p in info.get("pins", []):
        if p["name"] in ("Result", "InText", "RewindMonitorLine"):
            print(f"  {p['direction']:6} {p['name']:25} -> {p.get('connected_to')}")
