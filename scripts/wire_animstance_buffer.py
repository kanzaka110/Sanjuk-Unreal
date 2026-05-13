#!/usr/bin/env python3
"""Wire up UpdateAnimStanceWithBuffer using the existing node IDs."""

import json
import sys
import urllib.request

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "UpdateAnimStanceWithBuffer"
URL = "http://localhost:9316/mcp"
_msg_id = [2000]

# discovered IDs (from get_graph_summary)
N = {
    "entry_id": "K2Node_FunctionEntry_0",
    "get_anim": "K2Node_VariableGet_2",
    "eq1": "K2Node_EnumEquality_1",
    "branch_eq": "K2Node_IfThenElse_0",
    "set_accum_match": "K2Node_VariableSet_0",
    "get_anim_for_cand": "K2Node_VariableGet_3",
    "set_cand_match": "K2Node_VariableSet_1",
    "get_cand_eq2": "K2Node_VariableGet_4",
    "eq2": "K2Node_EnumEquality_2",
    "branch_cand_eq": "K2Node_IfThenElse_1",
    "get_accum_a": "K2Node_VariableGet_5",
    "get_delta_a": "K2Node_VariableGet_6",
    "accum_add": "K2Node_CallFunction_0",
    "set_accum_a": "K2Node_VariableSet_2",
    "set_cand_b": "K2Node_VariableSet_3",
    "get_delta_b": "K2Node_VariableGet_7",
    "set_accum_b": "K2Node_VariableSet_4",
    "get_accum_thr": "K2Node_VariableGet_8",
    "get_buf": "K2Node_VariableGet_9",
    "cmp_gt": "K2Node_CallFunction_1",
    "branch_apply": "K2Node_IfThenElse_2",
    "set_accum_zero_apply": "K2Node_VariableSet_5",
    "get_cand_apply": "K2Node_VariableGet_10",
    "set_anim_apply": "K2Node_VariableSet_6",
}


def call(action, params, ignore_errors=False):
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
        if ignore_errors:
            print(f"[WARN] {action} failed (ignored): {raw}", file=sys.stderr)
            return None
        print(f"[ERROR] action={action}\n  payload={params}\n  -> {raw}", file=sys.stderr)
        sys.exit(1)
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except Exception:
        return txt


def connect(k_from, from_pin, k_to, to_pin):
    return call(
        "connect_pins",
        {
            "asset_path": ASSET,
            "graph_name": GRAPH,
            "source_node": N[k_from],
            "source_pin": from_pin,
            "target_node": N[k_to],
            "target_pin": to_pin,
        },
    )


def set_pin(k_node, pin, value):
    return call(
        "set_pin_default",
        {
            "asset_path": ASSET,
            "graph_name": GRAPH,
            "node_id": N[k_node],
            "pin_name": pin,
            "value": value,
        },
    )


def main():
    # ---- pin defaults: literal 0 on accum-zero setter inputs
    set_pin("set_accum_match", "AnimStanceAccumulatedTime", "0.0")
    set_pin("set_accum_zero_apply", "AnimStanceAccumulatedTime", "0.0")
    print("[done] pin defaults")

    # ---- exec wiring
    connect("entry_id", "then", "branch_eq", "execute")
    connect("branch_eq", "then", "set_accum_match", "execute")
    connect("set_accum_match", "then", "set_cand_match", "execute")

    connect("branch_eq", "else", "branch_cand_eq", "execute")
    connect("branch_cand_eq", "then", "set_accum_a", "execute")
    connect("set_accum_a", "then", "branch_apply", "execute")
    connect("branch_cand_eq", "else", "set_cand_b", "execute")
    connect("set_cand_b", "then", "set_accum_b", "execute")
    connect("set_accum_b", "then", "branch_apply", "execute")

    connect("branch_apply", "then", "set_accum_zero_apply", "execute")
    connect("set_accum_zero_apply", "then", "set_anim_apply", "execute")
    print("[done] exec wiring")

    # ---- data wiring
    connect("entry_id", "NewStance", "eq1", "A")
    connect("get_anim", "AnimStance", "eq1", "B")
    connect("eq1", "ReturnValue", "branch_eq", "Condition")

    connect("get_anim_for_cand", "AnimStance", "set_cand_match", "CandidateAnimStance")

    connect("entry_id", "NewStance", "eq2", "A")
    connect("get_cand_eq2", "CandidateAnimStance", "eq2", "B")
    connect("eq2", "ReturnValue", "branch_cand_eq", "Condition")

    connect("get_accum_a", "AnimStanceAccumulatedTime", "accum_add", "A")
    connect("get_delta_a", "Delta Time", "accum_add", "B")
    connect("accum_add", "ReturnValue", "set_accum_a", "AnimStanceAccumulatedTime")

    connect("entry_id", "NewStance", "set_cand_b", "CandidateAnimStance")
    connect("get_delta_b", "Delta Time", "set_accum_b", "AnimStanceAccumulatedTime")

    connect("get_accum_thr", "AnimStanceAccumulatedTime", "cmp_gt", "A")
    connect("get_buf", "AnimStanceBufferTime", "cmp_gt", "B")
    connect("cmp_gt", "ReturnValue", "branch_apply", "Condition")

    connect("get_cand_apply", "CandidateAnimStance", "set_anim_apply", "AnimStance")
    print("[done] data wiring")


if __name__ == "__main__":
    main()
