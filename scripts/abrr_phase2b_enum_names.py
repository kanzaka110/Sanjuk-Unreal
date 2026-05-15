#!/usr/bin/env python3
"""ABRR Phase 2b: add the 4 missing K2Node_GetEnumeratorNameAsString nodes.

Try several function spellings, then fall back to direct K2Node hint via 'node_type'.
"""
from __future__ import annotations

import json
import urllib.request

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "AnimRewindRecorderEmit"
ENDPOINT = "http://localhost:9316/mcp"

# Old IDs and their positions from backup
TARGETS = [
    ("K2Node_GetEnumeratorNameAsString_3", [3760, 672]),
    ("K2Node_GetEnumeratorNameAsString_5", [5440, 1616]),
    ("K2Node_GetEnumeratorNameAsString_6", [3744, 576]),
    ("K2Node_GetEnumeratorNameAsString_7", [5168, 1408]),
]

CANDIDATES = [
    {"node_type": "function", "function_name": "GetEnumeratorName"},
    {"node_type": "function", "function_name": "GetEnumDisplayNameToString"},
    {"node_type": "function", "function_name": "Conv_EnumToString"},
    {"node_type": "GetEnumeratorNameAsString"},
    {"node_type": "EnumLiteral"},
    {"node_type": "function", "function_name": "GetEnumeratorUserFriendlyName"},
    {"node_type": "function", "function_name": "GetEnumDisplayNameByValue", "target_class": "KismetSystemLibrary"},
]


def rpc(action: str, params: dict) -> dict | str | None:
    body = {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "blueprint_query",
                   "arguments": {"action": action, "params": params}},
    }
    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    if data.get("result", {}).get("isError"):
        return {"_error": data["result"]["content"][0]["text"][:600]}
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except Exception:
        return txt


def try_candidates(pos: list[int]) -> tuple[str | None, str]:
    for cand in CANDIDATES:
        params: dict = {"asset_path": ASSET, "graph_name": GRAPH, "position": pos}
        params.update(cand)
        r = rpc("add_node", params)
        if isinstance(r, dict) and "_error" not in r:
            nid = r.get("node_id") or r.get("id")
            if nid:
                return nid, f"OK with {cand}"
        else:
            err = r.get("_error", "")[:120] if isinstance(r, dict) else str(r)[:120]
            print(f"  tried {cand}: {err}")
    return None, "ALL_FAILED"


def main() -> None:
    results = {}
    for old_id, pos in TARGETS:
        print(f"--- {old_id} at {pos} ---")
        nid, status = try_candidates(pos)
        print(f"  -> {nid} ({status})")
        results[old_id] = nid

    print("\n=== Summary ===")
    for k, v in results.items():
        print(f"  {k} -> {v}")


if __name__ == "__main__":
    main()
