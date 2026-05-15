#!/usr/bin/env python3
"""ABRR Phase 6: hook AnimRewindRecorderEmit at the END of UpdateValueFromPostEvaluation.

Strategy: insert ExecutionSequence right after FunctionEntry so both the original
branch and AnimRewindRecorderEmit call run every tick.

Final flow:
  FunctionEntry.then -> Sequence.execute
  Sequence.then_0    -> IfThenElse_0.execute (original branch)
  Sequence.then_1    -> CallFunction(AnimRewindRecorderEmit).execute

(Original wire FunctionEntry->IfThenElse must be disconnected first.)
"""
from __future__ import annotations

import json
import urllib.request

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "UpdateValueFromPostEvaluation"
ENDPOINT = "http://localhost:9316/mcp"


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


def step(label: str, action: str, params: dict) -> dict | str | None:
    print(f"\n--- {label} ---")
    print(f"  action={action} params={params}")
    r = rpc(action, params)
    print(f"  resp: {r}")
    return r


def main() -> None:
    # 1) Disconnect FunctionEntry.then -> IfThenElse_0.execute
    step("disconnect Entry->Branch", "disconnect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "source_node": "K2Node_FunctionEntry_0", "source_pin": "then",
        "target_node": "K2Node_IfThenElse_0", "target_pin": "execute",
    })

    # 2) Add ExecutionSequence
    seq_r = step("add ExecutionSequence", "add_node", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "node_type": "Sequence", "position": [200, 0],
    })
    if not isinstance(seq_r, dict) or "_error" in seq_r:
        print("ABORT: cannot add sequence")
        return
    seq_id = seq_r.get("node_id") or seq_r.get("id")

    # 3) Add CallFunction(AnimRewindRecorderEmit) on self
    call_r = step("add CallFunction(AnimRewindRecorderEmit)", "add_node", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "node_type": "function", "function_name": "AnimRewindRecorderEmit",
        "position": [600, 200],
    })
    if not isinstance(call_r, dict) or "_error" in call_r:
        print("ABORT: cannot add call")
        return
    call_id = call_r.get("node_id") or call_r.get("id")

    # 4) Wire Entry.then -> Sequence.execute
    step("wire Entry->Sequence", "connect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "source_node": "K2Node_FunctionEntry_0", "source_pin": "then",
        "target_node": seq_id, "target_pin": "execute",
    })

    # 5) Wire Sequence.then_0 -> IfThenElse_0.execute (original branch)
    step("wire Sequence.then_0 -> Branch", "connect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "source_node": seq_id, "source_pin": "then_0",
        "target_node": "K2Node_IfThenElse_0", "target_pin": "execute",
    })

    # 6) Wire Sequence.then_1 -> CallFunction(AnimRewindRecorderEmit).execute
    step("wire Sequence.then_1 -> AnimRewindRecorderEmit", "connect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "source_node": seq_id, "source_pin": "then_1",
        "target_node": call_id, "target_pin": "execute",
    })


if __name__ == "__main__":
    main()
