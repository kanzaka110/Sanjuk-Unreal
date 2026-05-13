#!/usr/bin/env python3
"""
PC_01_ABP: B_Lfoot 클립 재생 중 UpdateTargetRotation Strafe 분기 회전 보정 차단.

Phase 1 (already done via curl): add variable bIsPlayingTransitionBack (bool).

Phase 2 (this script):
    UpdateVariables 끝에 판정 노드 3개 + exec 연결:
        Get CurrentSequenceName
        EqualEqual_StrStr ('P_Player_Transition_Sprint_to_Battle_Jog_B_Lfoot')
        Set bIsPlayingTransitionBack
    ExecutionSequence_3 then_11 종단 (Set PrevWriggleMoveType) then 뒤로 chain.
    (ThreadSafe 안전 — read-only access to CurrentSequenceName + write bool)

Phase 3 (this script):
    UpdateTargetRotation Strafe 분기 게이트 (SelectFloat 패턴):
        K2Node_CallFunction_4 (NormalizeAxis) → K2Node_VariableSet_3.TargetRotationDelta  (기존)
    변경:
        K2Node_CallFunction_4.ReturnValue → SelectFloat.A
        literal 0.0 → SelectFloat.B
        Get bIsPlayingTransitionBack → NOT → SelectFloat.bPickA
        SelectFloat.ReturnValue → K2Node_VariableSet_3.TargetRotationDelta

Phase 4: compile_blueprint + save_asset
"""

import json
import sys
import urllib.request

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"
TARGET_CLIP = "P_Player_Transition_Sprint_to_Battle_Jog_B_Lfoot"

_msg_id = [3000]


def call(action, params):
    _msg_id[0] += 1
    body = {
        "jsonrpc": "2.0",
        "id": _msg_id[0],
        "method": "tools/call",
        "params": {
            "name": "blueprint_query",
            "arguments": {"action": action, "params": params},
        },
    }
    req = urllib.request.Request(
        URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8")
    data = json.loads(raw)
    if data.get("result", {}).get("isError"):
        print(f"[ERROR] action={action}\n  payload={params}\n  -> {raw}", file=sys.stderr)
        sys.exit(1)
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except Exception:
        return txt


def add_var_get(graph, var_name, position):
    out = call("add_node", {
        "asset_path": ASSET, "graph_name": graph,
        "node_type": "VariableGet", "variable_name": var_name,
        "position": position,
    })
    print(f"[+] {graph} VariableGet {var_name} -> {out['id']}")
    return out["id"]


def add_var_set(graph, var_name, position):
    out = call("add_node", {
        "asset_path": ASSET, "graph_name": graph,
        "node_type": "VariableSet", "variable_name": var_name,
        "position": position,
    })
    print(f"[+] {graph} VariableSet {var_name} -> {out['id']}")
    return out["id"]


def add_call(graph, func_name, target_class, position):
    out = call("add_node", {
        "asset_path": ASSET, "graph_name": graph,
        "node_type": "CallFunction",
        "function_name": func_name, "target_class": target_class,
        "position": position,
    })
    print(f"[+] {graph} CallFunction {target_class}::{func_name} -> {out['id']}")
    return out["id"]


def connect(graph, src_node, src_pin, tgt_node, tgt_pin):
    out = call("connect_pins", {
        "asset_path": ASSET, "graph_name": graph,
        "source_node": src_node, "source_pin": src_pin,
        "target_node": tgt_node, "target_pin": tgt_pin,
    })
    print(f"  -> connect {graph}: {src_node}.{src_pin} -> {tgt_node}.{tgt_pin}")
    return out


def disconnect(graph, src_node, src_pin, tgt_node, tgt_pin):
    out = call("disconnect_pins", {
        "asset_path": ASSET, "graph_name": graph,
        "source_node": src_node, "source_pin": src_pin,
        "target_node": tgt_node, "target_pin": tgt_pin,
    })
    print(f"  -> disconnect {graph}: {src_node}.{src_pin} -X- {tgt_node}.{tgt_pin}")
    return out


def set_pin(graph, node_id, pin_name, value):
    out = call("set_pin_default", {
        "asset_path": ASSET, "graph_name": graph,
        "node_id": node_id, "pin_name": pin_name, "value": value,
    })
    print(f"  -> set_pin {graph}: {node_id}.{pin_name} = {value!r}")
    return out


def get_node(graph, node_id):
    return call("get_node_details", {
        "asset_path": ASSET, "graph_name": graph, "node_id": node_id,
    })


# -------------------------------------------------------------------
# Phase 2: UpdateVariables
# -------------------------------------------------------------------
def phase2_update_variables():
    print("\n=== Phase 2: UpdateVariables ===")
    graph = "UpdateVariables"

    # 1) Add 3 nodes near top-right empty area
    # Place at y=2700 (below current dense layout)
    node_get_seq = add_var_get(graph, "CurrentSequenceName", [3200, 2700])
    node_eq = add_call(graph, "EqualEqual_StrStr", "KismetStringLibrary", [3460, 2700])
    node_set_back = add_var_set(graph, "bIsPlayingTransitionBack", [3760, 2700])

    # 2) Inspect EqualEqual_StrStr pin names
    eq_details = get_node(graph, node_eq)
    print(f"  eq pins: {[p['name'] for p in eq_details['pins']]}")

    # 3) Set literal pin B to target clip name
    # Use 'B' as the second-string pin
    set_pin(graph, node_eq, "B", TARGET_CLIP)

    # 4) Connect data: Get CurrentSequenceName -> eq.A
    connect(graph, node_get_seq, "CurrentSequenceName", node_eq, "A")
    # 5) eq.ReturnValue -> Set bIsPlayingTransitionBack input
    connect(graph, node_eq, "ReturnValue", node_set_back, "bIsPlayingTransitionBack")

    # 6) Exec chain: chain to end of ExecutionSequence_3.then_11
    # then_11 -> K2Node_Knot_1 -> Set bPrevIsWriggling -> Set bIsWriggling -> ... -> Set WriggleMoveType -> K2Node_IfThenElse_3 (Branch terminal)
    # Safest insertion point: after the LAST exec leaf on the then_11 chain.
    # From dump: the chain ends at "K2Node_IfThenElse_3 Branch" (terminal). Its then is empty.
    # We append to that Branch.then.
    # Verify via get_node_details first
    branch_term = get_node(graph, "K2Node_IfThenElse_3")
    then_pin = next((p for p in branch_term["pins"]
                    if p["direction"] == "output" and p["name"] == "then"), None)
    if then_pin and then_pin.get("connected_to"):
        print(f"[WARN] K2Node_IfThenElse_3.then already connected -> {then_pin['connected_to']}; using alternative insertion point")
        # Fallback: use ExecutionSequence_3 then_12 (try to add new pin)
        connect(graph, "K2Node_ExecutionSequence_3", "then_12", node_set_back, "execute")
    else:
        connect(graph, "K2Node_IfThenElse_3", "then", node_set_back, "execute")

    print("[OK] Phase 2 complete")
    return node_get_seq, node_eq, node_set_back


# -------------------------------------------------------------------
# Phase 3: UpdateTargetRotation
# -------------------------------------------------------------------
def phase3_update_target_rotation():
    print("\n=== Phase 3: UpdateTargetRotation ===")
    graph = "UpdateTargetRotation"

    # Existing wiring:
    #   K2Node_CallFunction_4.ReturnValue -> K2Node_VariableSet_3.TargetRotationDelta
    # New gate:
    #   K2Node_CallFunction_4.ReturnValue -> SelectFloat.A
    #   literal 0.0 -> SelectFloat.B
    #   Get bIsPlayingTransitionBack -> NOT -> SelectFloat.bPickA
    #   SelectFloat.ReturnValue -> K2Node_VariableSet_3.TargetRotationDelta

    # 1) Add SelectFloat (KismetMathLibrary::SelectFloat)
    node_select = add_call(graph, "SelectFloat", "KismetMathLibrary", [2080, 720])
    # 2) Add Get bIsPlayingTransitionBack
    node_get_back = add_var_get(graph, "bIsPlayingTransitionBack", [1840, 568])
    # 3) Add NOT (Not_PreBool)
    node_not = add_call(graph, "Not_PreBool", "KismetMathLibrary", [1990, 596])

    # Inspect new node pins
    sel_details = get_node(graph, node_select)
    print(f"  SelectFloat pins: {[(p['name'], p['direction']) for p in sel_details['pins']]}")
    not_details = get_node(graph, node_not)
    print(f"  Not_PreBool pins: {[(p['name'], p['direction']) for p in not_details['pins']]}")

    # 4) Disconnect existing CF4 -> Set_3
    disconnect(graph, "K2Node_CallFunction_4", "ReturnValue",
               "K2Node_VariableSet_3", "TargetRotationDelta")

    # 5) Connect new gate
    connect(graph, "K2Node_CallFunction_4", "ReturnValue", node_select, "A")
    connect(node_select, "ReturnValue", "K2Node_VariableSet_3", "TargetRotationDelta")
    # B pin: literal 0.0
    set_pin(graph, node_select, "B", "0.0")
    # bPickA: Get back -> NOT -> bPickA
    connect(graph, node_get_back, "bIsPlayingTransitionBack", node_not, "A")
    connect(graph, node_not, "ReturnValue", node_select, "bPickA")

    print("[OK] Phase 3 complete")
    return node_select, node_get_back, node_not


# -------------------------------------------------------------------
# Phase 4: compile + save
# -------------------------------------------------------------------
def phase4_compile_save():
    print("\n=== Phase 4: compile + save ===")
    out_c = call("compile_blueprint", {"asset_path": ASSET})
    print(f"  compile: {out_c}")
    out_s = call("save_asset", {"asset_path": ASSET})
    print(f"  save:    {out_s}")


def main():
    phase2_update_variables()
    phase3_update_target_rotation()
    phase4_compile_save()
    print("\n[ALL DONE]")


if __name__ == "__main__":
    main()
