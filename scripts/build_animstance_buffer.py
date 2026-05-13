#!/usr/bin/env python3
"""
Build UpdateAnimStanceWithBuffer function graph in PC_01_ABP via Monolith HTTP API.

Logic:
    if NewStance == AnimStance:
        AnimStanceAccumulatedTime = 0
        CandidateAnimStance = AnimStance
        return  (AnimStance unchanged)
    else:
        if NewStance == CandidateAnimStance:
            AnimStanceAccumulatedTime += DeltaTime
        else:
            CandidateAnimStance = NewStance
            AnimStanceAccumulatedTime = DeltaTime

        if AnimStanceAccumulatedTime > AnimStanceBufferTime:
            AnimStanceAccumulatedTime = 0
            Set AnimStance = CandidateAnimStance
        else:
            (do nothing)
"""

import json
import sys
import urllib.request

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "UpdateAnimStanceWithBuffer"
URL = "http://localhost:9316/mcp"
_msg_id = [1000]


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


def add_var_get(var_name, position):
    out = call(
        "add_node",
        {
            "asset_path": ASSET,
            "graph_name": GRAPH,
            "node_type": "VariableGet",
            "variable_name": var_name,
            "position": position,
        },
    )
    return out["id"]


def add_var_set(var_name, position):
    out = call(
        "add_node",
        {
            "asset_path": ASSET,
            "graph_name": GRAPH,
            "node_type": "VariableSet",
            "variable_name": var_name,
            "position": position,
        },
    )
    return out["id"]


def add_branch(position):
    out = call(
        "add_node",
        {
            "asset_path": ASSET,
            "graph_name": GRAPH,
            "node_type": "Branch",
            "position": position,
        },
    )
    return out["id"]


def add_enum_eq(position):
    # Use Equal_ByteByte CallFunction so byte-byte (input pin or variable) connects cleanly
    out = call(
        "add_node",
        {
            "asset_path": ASSET,
            "graph_name": GRAPH,
            "node_type": "CallFunction",
            "function_name": "EqualEqual_ByteByte",
            "target_class": "KismetMathLibrary",
            "position": position,
        },
    )
    return out["id"]


def add_call(func_name, target_class, position):
    out = call(
        "add_node",
        {
            "asset_path": ASSET,
            "graph_name": GRAPH,
            "node_type": "CallFunction",
            "function_name": func_name,
            "target_class": target_class,
            "position": position,
        },
    )
    return out["id"]


def connect(from_node, from_pin, to_node, to_pin):
    return call(
        "connect_pins",
        {
            "asset_path": ASSET,
            "graph_name": GRAPH,
            "source_node": from_node,
            "source_pin": from_pin,
            "target_node": to_node,
            "target_pin": to_pin,
        },
    )


def set_pin(node, pin, value):
    return call(
        "set_pin_default",
        {
            "asset_path": ASSET,
            "graph_name": GRAPH,
            "node_id": node,
            "pin_name": pin,
            "value": value,
        },
    )


def get_node(node_id):
    return call(
        "get_node_details",
        {
            "asset_path": ASSET,
            "graph_name": GRAPH,
            "node_id": node_id,
        },
    )


def main():
    summary = call("get_graph_summary", {"asset_path": ASSET, "graph_name": GRAPH})
    entry_id = None
    for n in summary["nodes"]:
        if n["class"] == "K2Node_FunctionEntry":
            entry_id = n["id"]
            break
    assert entry_id, "FunctionEntry not found"
    print(f"entry: {entry_id}")

    # Branch1 cond: NewStance == AnimStance
    get_anim = add_var_get("AnimStance", [200, 400])
    eq1 = add_enum_eq([400, 380])
    branch_eq = add_branch([600, 0])
    print(f"branch_eq: {branch_eq}, eq1: {eq1}, get_anim: {get_anim}")

    # match path
    set_accum_match = add_var_set("AnimStanceAccumulatedTime", [850, 0])
    get_anim_for_cand = add_var_get("AnimStance", [900, 200])
    set_cand_match = add_var_set("CandidateAnimStance", [1150, 0])

    # else path: Branch2 cond NewStance == CandidateAnimStance
    get_cand_eq2 = add_var_get("CandidateAnimStance", [600, 600])
    eq2 = add_enum_eq([800, 580])
    branch_cand_eq = add_branch([1000, 400])

    # path A: Accum += DeltaTime
    get_accum_a = add_var_get("AnimStanceAccumulatedTime", [1200, 350])
    get_delta_a = add_var_get("Delta Time", [1200, 410])
    accum_add = add_call("Add_DoubleDouble", "KismetMathLibrary", [1400, 380])
    set_accum_a = add_var_set("AnimStanceAccumulatedTime", [1600, 350])

    # path B: Candidate = NewStance, Accum = DeltaTime
    set_cand_b = add_var_set("CandidateAnimStance", [1200, 600])
    get_delta_b = add_var_get("Delta Time", [1300, 750])
    set_accum_b = add_var_set("AnimStanceAccumulatedTime", [1500, 600])

    # converge Branch3 cond: Accum > BufferTime
    get_accum_thr = add_var_get("AnimStanceAccumulatedTime", [1850, 500])
    get_buf = add_var_get("AnimStanceBufferTime", [1850, 560])
    cmp_gt = add_call("Greater_DoubleDouble", "KismetMathLibrary", [2050, 530])
    branch_apply = add_branch([2250, 500])

    # apply
    set_accum_zero_apply = add_var_set("AnimStanceAccumulatedTime", [2450, 450])
    get_cand_apply = add_var_get("CandidateAnimStance", [2550, 600])
    set_anim_apply = add_var_set("AnimStance", [2750, 450])

    print("[done] nodes created")

    # pin defaults: literal zero (input pin name == variable name)
    set_pin(set_accum_match, "AnimStanceAccumulatedTime", "0.0")
    set_pin(set_accum_zero_apply, "AnimStanceAccumulatedTime", "0.0")
    print("[done] pin defaults")

    # exec wiring
    connect(entry_id, "then", branch_eq, "execute")
    connect(branch_eq, "then", set_accum_match, "execute")
    connect(set_accum_match, "then", set_cand_match, "execute")

    connect(branch_eq, "else", branch_cand_eq, "execute")
    connect(branch_cand_eq, "then", set_accum_a, "execute")
    connect(set_accum_a, "then", branch_apply, "execute")
    connect(branch_cand_eq, "else", set_cand_b, "execute")
    connect(set_cand_b, "then", set_accum_b, "execute")
    connect(set_accum_b, "then", branch_apply, "execute")

    connect(branch_apply, "then", set_accum_zero_apply, "execute")
    connect(set_accum_zero_apply, "then", set_anim_apply, "execute")
    print("[done] exec wiring")

    # data wiring
    # eq1: A=NewStance, B=AnimStance
    connect(entry_id, "NewStance", eq1, "A")
    connect(get_anim, "AnimStance", eq1, "B")
    connect(eq1, "ReturnValue", branch_eq, "Condition")

    # SetCand match input = Get AnimStance
    connect(get_anim_for_cand, "AnimStance", set_cand_match, "CandidateAnimStance")

    # eq2: A=NewStance, B=Candidate
    connect(entry_id, "NewStance", eq2, "A")
    connect(get_cand_eq2, "CandidateAnimStance", eq2, "B")
    connect(eq2, "ReturnValue", branch_cand_eq, "Condition")

    # Accum + Delta -> Set Accum
    connect(get_accum_a, "AnimStanceAccumulatedTime", accum_add, "A")
    connect(get_delta_a, "Delta Time", accum_add, "B")
    connect(accum_add, "ReturnValue", set_accum_a, "AnimStanceAccumulatedTime")

    # SetCand_b input = NewStance ; SetAccum_b input = DeltaTime
    connect(entry_id, "NewStance", set_cand_b, "CandidateAnimStance")
    connect(get_delta_b, "Delta Time", set_accum_b, "AnimStanceAccumulatedTime")

    # cmp_gt cond
    connect(get_accum_thr, "AnimStanceAccumulatedTime", cmp_gt, "A")
    connect(get_buf, "AnimStanceBufferTime", cmp_gt, "B")
    connect(cmp_gt, "ReturnValue", branch_apply, "Condition")

    # apply: Set AnimStance = Candidate
    connect(get_cand_apply, "CandidateAnimStance", set_anim_apply, "AnimStance")
    print("[done] data wiring")

    # save node-id map for downstream
    nodemap = {
        "entry_id": entry_id,
        "get_anim": get_anim,
        "eq1": eq1,
        "branch_eq": branch_eq,
        "set_accum_match": set_accum_match,
        "get_anim_for_cand": get_anim_for_cand,
        "set_cand_match": set_cand_match,
        "get_cand_eq2": get_cand_eq2,
        "eq2": eq2,
        "branch_cand_eq": branch_cand_eq,
        "get_accum_a": get_accum_a,
        "get_delta_a": get_delta_a,
        "accum_add": accum_add,
        "set_accum_a": set_accum_a,
        "set_cand_b": set_cand_b,
        "get_delta_b": get_delta_b,
        "set_accum_b": set_accum_b,
        "get_accum_thr": get_accum_thr,
        "get_buf": get_buf,
        "cmp_gt": cmp_gt,
        "branch_apply": branch_apply,
        "set_accum_zero_apply": set_accum_zero_apply,
        "get_cand_apply": get_cand_apply,
        "set_anim_apply": set_anim_apply,
    }
    with open(r"scripts/dumps/_build_nodemap.json", "w", encoding="utf-8") as f:
        json.dump(nodemap, f, indent=2)
    print(json.dumps(nodemap, indent=2))


if __name__ == "__main__":
    main()
