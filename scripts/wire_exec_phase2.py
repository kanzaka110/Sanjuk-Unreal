#!/usr/bin/env python3
"""
Wire exec chain for Phase 2: insert Set bIsPlayingTransitionBack
between K2Node_VariableSet_47.then and K2Node_IfThenElse_3.execute.
"""
import json, sys, urllib.request

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"
_msg_id = [4000]


def call(action, params):
    _msg_id[0] += 1
    body = {"jsonrpc":"2.0","id":_msg_id[0],"method":"tools/call",
            "params":{"name":"blueprint_query","arguments":{"action":action,"params":params}}}
    req = urllib.request.Request(URL, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8")
    data = json.loads(raw)
    if data.get("result",{}).get("isError"):
        print(f"[ERROR] action={action}\n payload={params}\n -> {raw}", file=sys.stderr)
        sys.exit(1)
    txt = data["result"]["content"][0]["text"]
    try: return json.loads(txt)
    except Exception: return txt


graph = "UpdateVariables"
new_set = "K2Node_VariableSet_37"  # Set bIsPlayingTransitionBack created earlier

# Disconnect K2Node_VariableSet_47.then -> K2Node_IfThenElse_3.execute
print("[1] disconnect VariableSet_47.then -> IfThenElse_3.execute")
out = call("disconnect_pins", {
    "asset_path": ASSET, "graph_name": graph,
    "node_id": "K2Node_VariableSet_47", "pin_name": "then",
    "target_node": "K2Node_IfThenElse_3", "target_pin": "execute",
})
print(f"  -> {out}")

# Connect VariableSet_47.then -> new_set.execute
print("[2] connect VariableSet_47.then -> new_set.execute")
out = call("connect_pins", {
    "asset_path": ASSET, "graph_name": graph,
    "source_node": "K2Node_VariableSet_47", "source_pin": "then",
    "target_node": new_set, "target_pin": "execute",
})
print(f"  -> {out}")

# Connect new_set.then -> IfThenElse_3.execute
print("[3] connect new_set.then -> IfThenElse_3.execute")
out = call("connect_pins", {
    "asset_path": ASSET, "graph_name": graph,
    "source_node": new_set, "source_pin": "then",
    "target_node": "K2Node_IfThenElse_3", "target_pin": "execute",
})
print(f"  -> {out}")

print("[OK] exec wiring done")
