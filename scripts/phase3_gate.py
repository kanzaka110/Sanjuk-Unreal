#!/usr/bin/env python3
"""
Phase 3: UpdateTargetRotation Strafe branch gate.

Existing:
    K2Node_CallFunction_4 (NormalizeAxis).ReturnValue -> K2Node_VariableSet_3.TargetRotationDelta

New gate:
    K2Node_CallFunction_4.ReturnValue -> SelectFloat.A
    literal 0.0 -> SelectFloat.B
    Get bIsPlayingTransitionBack -> NOT -> SelectFloat.bPickA
    SelectFloat.ReturnValue -> K2Node_VariableSet_3.TargetRotationDelta
"""
import json, sys, urllib.request

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"
GRAPH = "UpdateTargetRotation"
_msg_id = [5000]


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


def add_node(node_type, position, **kwargs):
    params = {"asset_path": ASSET, "graph_name": GRAPH,
              "node_type": node_type, "position": position}
    params.update(kwargs)
    out = call("add_node", params)
    print(f"[+] {node_type} {kwargs} -> {out['id']}")
    return out["id"]


def connect(sn, sp, tn, tp):
    out = call("connect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "source_node": sn, "source_pin": sp,
        "target_node": tn, "target_pin": tp,
    })
    print(f"  -> connect {sn}.{sp} -> {tn}.{tp}")
    return out


def disconnect(node_id, pin_name, target_node=None, target_pin=None):
    p = {"asset_path": ASSET, "graph_name": GRAPH,
         "node_id": node_id, "pin_name": pin_name}
    if target_node:
        p["target_node"] = target_node
        p["target_pin"] = target_pin
    out = call("disconnect_pins", p)
    print(f"  -> disconnect {node_id}.{pin_name}")
    return out


def set_pin(node_id, pin_name, value):
    out = call("set_pin_default", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "node_id": node_id, "pin_name": pin_name, "value": value,
    })
    print(f"  -> set_pin {node_id}.{pin_name} = {value!r}")
    return out


def get_node(node_id):
    return call("get_node_details", {
        "asset_path": ASSET, "graph_name": GRAPH, "node_id": node_id,
    })


# 1) Create SelectFloat, Get bIsPlayingTransitionBack, Not_PreBool
sel = add_node("CallFunction", [2080, 720],
               function_name="SelectFloat", target_class="KismetMathLibrary")
get_back = add_node("VariableGet", [1840, 568],
                    variable_name="bIsPlayingTransitionBack")
not_bool = add_node("CallFunction", [1990, 596],
                    function_name="Not_PreBool", target_class="KismetMathLibrary")

# 2) Inspect SelectFloat pins
sd = get_node(sel)
print(f"  SelectFloat pins: {[(p['name'], p['direction'], p.get('type')) for p in sd['pins']]}")
nd = get_node(not_bool)
print(f"  Not_PreBool pins: {[(p['name'], p['direction'], p.get('type')) for p in nd['pins']]}")

# 3) Disconnect existing CF4 -> Set_3
disconnect("K2Node_CallFunction_4", "ReturnValue",
           "K2Node_VariableSet_3", "TargetRotationDelta")

# 4) Wire new gate
connect("K2Node_CallFunction_4", "ReturnValue", sel, "A")
connect(sel, "ReturnValue", "K2Node_VariableSet_3", "TargetRotationDelta")
set_pin(sel, "B", "0.0")
connect(get_back, "bIsPlayingTransitionBack", not_bool, "A")
connect(not_bool, "ReturnValue", sel, "bPickA")

print("\n[OK] Phase 3 wiring done")
