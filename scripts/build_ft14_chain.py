#!/usr/bin/env python3
"""Add FT14 + 5 fields (sms, vac, na, rrt, rrr) to AnimRewindRecorderEmit.

Strategy:
  1) Add K2Node_FormatText with format string -> creates the argument pins automatically.
  2) Add Conv_ByteToString CallFunction (Kismet) for StateMachineMoveState.
  3) Add Array_Length CallFunction for ValidAnimFromChooser.
  4) Add 5 VariableGet nodes (StateMachineMoveState, ValidAnimFromChooser, NullAnim, RunRetransit, RetransitReason).
  5) Connect everything; reroute FT_12.Result downstream into new FT.prev,
     new FT.Result -> CallFunction_4.InText AND VariableSet_1.RewindMonitorLine.
"""
import json
import urllib.request
import sys

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "AnimRewindRecorderEmit"
ENDPOINT = "http://localhost:9316/mcp"

def rpc(action, params, _id=1):
    body = {
        "jsonrpc": "2.0",
        "id": _id,
        "method": "tools/call",
        "params": {
            "name": "blueprint_query",
            "arguments": {"action": action, "params": params},
        },
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
    data = json.loads(raw)
    if data.get("result", {}).get("isError"):
        msg = data['result']['content'][0]['text']
        print(f"!! {action} ERROR: {msg[:600]}", file=sys.stderr)
        return None
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except Exception:
        return txt


def add_node(node_type, x, y, extra=None):
    p = {
        "asset_path": ASSET,
        "graph_name": GRAPH,
        "node_type": node_type,
        "position": [x, y],
    }
    if extra:
        p.update(extra)
    return rpc("add_node", p)


def connect(src_node, src_pin, tgt_node, tgt_pin):
    return rpc("connect_pins", {
        "asset_path": ASSET,
        "graph_name": GRAPH,
        "source_node": src_node,
        "source_pin": src_pin,
        "target_node": tgt_node,
        "target_pin": tgt_pin,
    })


def disconnect(src_node, src_pin, tgt_node, tgt_pin):
    return rpc("disconnect_pins", {
        "asset_path": ASSET,
        "graph_name": GRAPH,
        "source_node": src_node,
        "source_pin": src_pin,
        "target_node": tgt_node,
        "target_pin": tgt_pin,
    })


def main():
    print("=== Step 1: add 5 VariableGet nodes ===")
    base_x, base_y = 6000, 980
    vars_to_add = [
        ("StateMachineMoveState", base_x, base_y + 0),
        ("ValidAnimFromChooser",  base_x, base_y + 80),
        ("NullAnim",              base_x, base_y + 160),
        ("RunRetransit",          base_x, base_y + 240),
        ("RetransitReason",       base_x, base_y + 320),
    ]
    var_ids = {}
    for name, x, y in vars_to_add:
        r = add_node("get", x, y, extra={"variable_name": name})
        if not r:
            sys.exit(f"failed to add Get {name}")
        nid = r.get("node_id") or r.get("id")
        print(f"  Get {name} -> {nid}")
        var_ids[name] = nid

    print("\n=== Step 2: add Conv_ByteToString CallFunction ===")
    r = add_node("function", base_x + 240, base_y + 0, extra={
        "function_name": "Conv_ByteToString",
        "target_class": "KismetStringLibrary",
    })
    if not r:
        sys.exit("failed to add Conv_ByteToString")
    btos_id = r.get("node_id") or r.get("id")
    print(f"  Conv_ByteToString -> {btos_id}")

    print("\n=== Step 3: add Array_Length ===")
    r = add_node("function", base_x + 240, base_y + 80, extra={
        "function_name": "Array_Length",
        "target_class": "KismetArrayLibrary",
    })
    if not r:
        sys.exit("failed to add Array_Length")
    arrlen_id = r.get("node_id") or r.get("id")
    print(f"  Array_Length -> {arrlen_id}")

    print("\n=== Step 4: add new K2Node_FormatText ===")
    fmt_str = '{prev},"sms"={sms},"vac"={vac},"na"={na},"rrt"={rrt},"rrr"={rrr}'
    r = add_node("format_text", 6400, 768, extra={"format": fmt_str})
    if not r:
        sys.exit("failed to add FormatText")
    ft_id = r.get("node_id") or r.get("id")
    print(f"  new FT -> {ft_id}")

    print("\n=== Step 5: wire helpers -> FT inputs ===")
    # sms <- Conv_ByteToString(StateMachineMoveState)
    print(connect(var_ids["StateMachineMoveState"], "StateMachineMoveState", btos_id, "InByte"))
    print(connect(btos_id, "ReturnValue", ft_id, "sms"))
    # vac <- Array_Length(ValidAnimFromChooser)
    print(connect(var_ids["ValidAnimFromChooser"], "ValidAnimFromChooser", arrlen_id, "TargetArray"))
    print(connect(arrlen_id, "ReturnValue", ft_id, "vac"))
    # na/rrt/rrr direct
    print(connect(var_ids["NullAnim"], "NullAnim", ft_id, "na"))
    print(connect(var_ids["RunRetransit"], "RunRetransit", ft_id, "rrt"))
    print(connect(var_ids["RetransitReason"], "RetransitReason", ft_id, "rrr"))

    print("\n=== Step 6: rewire FT_12.Result downstream ===")
    print(disconnect("K2Node_FormatText_12", "Result", "K2Node_CallFunction_4", "InText"))
    print(disconnect("K2Node_FormatText_12", "Result", "K2Node_VariableSet_1", "RewindMonitorLine"))
    print(connect("K2Node_FormatText_12", "Result", ft_id, "prev"))
    print(connect(ft_id, "Result", "K2Node_CallFunction_4", "InText"))
    print(connect(ft_id, "Result", "K2Node_VariableSet_1", "RewindMonitorLine"))

    print("\n=== Step 7: compile ===")
    r = rpc("compile_blueprint", {"asset_path": ASSET})
    print("compile:", r)

    print("\nDONE. New IDs:")
    print("  FormatText:", ft_id)
    print("  Conv_ByteToString:", btos_id)
    print("  Array_Length:", arrlen_id)
    for k,v in var_ids.items():
        print(f"  Get {k}:", v)

if __name__ == "__main__":
    main()
