#!/usr/bin/env python3
"""
PC_01_ABP — Transition 회전 보정 차단 게이트 (4패턴 확장).

매트릭스 처방 ①. 2026-05-15.

5/13 작업의 1패턴(EqualEqual_StrStr) 게이트가 5/14 ABP 손상 과정에서 분실됨.
처음부터 4패턴(Contains) 게이트로 재구축.

매칭 룰:
    bIsPlayingTransitionBack =
        Contains(CurrentSequenceName, "Sprint_to_Battle") OR
        Contains(CurrentSequenceName, "Sprint_to_LockOn") OR
        Contains(CurrentSequenceName, "Sprint_to_Jog") OR
        (Contains(CurrentSequenceName, "Transition_") AND IsLockOn)

Phases:
    1. 변수 추가: bIsPlayingTransitionBack (bool, Buffer)
    2. UpdateVariables: Get×2 + Contains×4 + AND×1 + OR×3 + Set + exec chain
    3. UpdateTargetRotation: SelectFloat + Not + Get 게이트 (NormalizeAxis → SelectFloat.A, 0 → B)
    4. compile_blueprint + save_asset

ThreadSafe: CurrentSequenceName/IsLockOn read-only, bIsPlayingTransitionBack write only.
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("phase1_extend")

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"
VAR_NAME = "bIsPlayingTransitionBack"
PATTERNS = ["Sprint_to_Battle", "Sprint_to_LockOn", "Sprint_to_Jog", "Transition_"]

_msg_id = [4000]


def call(action: str, params: dict[str, Any]) -> Any:
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
        log.error("[ERROR] action=%s params=%s -> %s", action, params, raw)
        sys.exit(1)
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return txt


def add_var(name: str, var_type: str, category: str, default: str = "false") -> Any:
    out = call(
        "add_variable",
        {
            "asset_path": ASSET,
            "name": name,
            "type": var_type,
            "category": category,
            "default_value": default,
            "instance_editable": False,
            "blueprint_read_only": False,
        },
    )
    log.info("[+] add_variable %s (%s) -> %s", name, var_type, out)
    return out


def add_node(graph: str, node_type: str, position: list[int], **kwargs: Any) -> str:
    params = {
        "asset_path": ASSET,
        "graph_name": graph,
        "node_type": node_type,
        "position": position,
        **kwargs,
    }
    out = call("add_node", params)
    nid = out["id"] if isinstance(out, dict) else out
    log.info("[+] %s %s -> %s", graph, kwargs.get("function_name") or kwargs.get("variable_name") or node_type, nid)
    return nid


def add_var_get(graph: str, var_name: str, position: list[int]) -> str:
    return add_node(graph, "VariableGet", position, variable_name=var_name)


def add_var_set(graph: str, var_name: str, position: list[int]) -> str:
    return add_node(graph, "VariableSet", position, variable_name=var_name)


def add_call(graph: str, func_name: str, target_class: str, position: list[int]) -> str:
    return add_node(
        graph,
        "CallFunction",
        position,
        function_name=func_name,
        target_class=target_class,
    )


def connect(graph: str, src: str, src_pin: str, tgt: str, tgt_pin: str) -> Any:
    out = call(
        "connect_pins",
        {
            "asset_path": ASSET,
            "graph_name": graph,
            "source_node": src,
            "source_pin": src_pin,
            "target_node": tgt,
            "target_pin": tgt_pin,
        },
    )
    log.info("  link %s: %s.%s -> %s.%s", graph, src, src_pin, tgt, tgt_pin)
    return out


def set_pin(graph: str, node_id: str, pin_name: str, value: str) -> Any:
    out = call(
        "set_pin_default",
        {
            "asset_path": ASSET,
            "graph_name": graph,
            "node_id": node_id,
            "pin_name": pin_name,
            "value": value,
        },
    )
    log.info("  set %s: %s.%s = %r", graph, node_id, pin_name, value)
    return out


# ---------------------------------------------------------------------------
# Phase 1: variable
# ---------------------------------------------------------------------------
def phase1_variable() -> None:
    log.info("\n=== Phase 1: variable ===")
    add_var(VAR_NAME, "bool", "Buffer", default="false")


# ---------------------------------------------------------------------------
# Phase 2: UpdateVariables — Get×2 + Contains×4 + AND + OR×3 + Set
# ---------------------------------------------------------------------------
def phase2_update_variables() -> dict[str, str]:
    log.info("\n=== Phase 2: UpdateVariables ===")
    graph = "UpdateVariables"

    seq_get = add_var_get(graph, "CurrentSequenceName", [4800, 2700])
    lock_get = add_var_get(graph, "IsLockOn", [4800, 2920])

    contains_ids: list[str] = []
    for i, pat in enumerate(PATTERNS):
        cid = add_call(graph, "Contains", "KismetStringLibrary", [5100, 2600 + i * 80])
        set_pin(graph, cid, "Substring", pat)
        connect(graph, seq_get, "CurrentSequenceName", cid, "SearchIn")
        contains_ids.append(cid)

    # AND(Contains("Transition_"), IsLockOn)
    and_id = add_call(graph, "BooleanAND", "KismetMathLibrary", [5400, 2890])
    connect(graph, contains_ids[3], "ReturnValue", and_id, "A")
    connect(graph, lock_get, "IsLockOn", and_id, "B")

    # OR chain: ((Battle | LockOn) | Jog) | AND
    or1 = add_call(graph, "BooleanOR", "KismetMathLibrary", [5400, 2630])
    connect(graph, contains_ids[0], "ReturnValue", or1, "A")
    connect(graph, contains_ids[1], "ReturnValue", or1, "B")

    or2 = add_call(graph, "BooleanOR", "KismetMathLibrary", [5560, 2700])
    connect(graph, or1, "ReturnValue", or2, "A")
    connect(graph, contains_ids[2], "ReturnValue", or2, "B")

    or3 = add_call(graph, "BooleanOR", "KismetMathLibrary", [5720, 2790])
    connect(graph, or2, "ReturnValue", or3, "A")
    connect(graph, and_id, "ReturnValue", or3, "B")

    set_id = add_var_set(graph, VAR_NAME, [5950, 2790])
    connect(graph, or3, "ReturnValue", set_id, VAR_NAME)

    # exec chain — append to K2Node_ExecutionSequence_3 (new pin then_13)
    connect(graph, "K2Node_ExecutionSequence_3", "then_13", set_id, "execute")

    log.info("[OK] Phase 2 done. set_id=%s", set_id)
    return {
        "seq_get": seq_get,
        "lock_get": lock_get,
        "contains": ",".join(contains_ids),
        "and": and_id,
        "or1": or1,
        "or2": or2,
        "or3": or3,
        "set": set_id,
    }


# ---------------------------------------------------------------------------
# Phase 3: UpdateTargetRotation Strafe gate
# ---------------------------------------------------------------------------
def phase3_target_rotation() -> dict[str, str]:
    log.info("\n=== Phase 3: UpdateTargetRotation ===")
    graph = "UpdateTargetRotation"

    sel = add_call(graph, "SelectFloat", "KismetMathLibrary", [2080, 720])
    get_back = add_var_get(graph, VAR_NAME, [1840, 568])
    not_id = add_call(graph, "Not_PreBool", "KismetMathLibrary", [1990, 596])

    # Disconnect existing CF4 -> Set_3.TargetRotationDelta
    call(
        "disconnect_pins",
        {
            "asset_path": ASSET,
            "graph_name": graph,
            "source_node": "K2Node_CallFunction_4",
            "source_pin": "ReturnValue",
            "target_node": "K2Node_VariableSet_3",
            "target_pin": "TargetRotationDelta",
        },
    )
    log.info("  disconnect K2Node_CallFunction_4.ReturnValue -X- K2Node_VariableSet_3.TargetRotationDelta")

    connect(graph, "K2Node_CallFunction_4", "ReturnValue", sel, "A")
    set_pin(graph, sel, "B", "0.0")
    connect(graph, get_back, VAR_NAME, not_id, "A")
    connect(graph, not_id, "ReturnValue", sel, "bPickA")
    connect(graph, sel, "ReturnValue", "K2Node_VariableSet_3", "TargetRotationDelta")

    log.info("[OK] Phase 3 done. sel=%s", sel)
    return {"sel": sel, "not": not_id, "get_back": get_back}


# ---------------------------------------------------------------------------
# Phase 4: compile + save
# ---------------------------------------------------------------------------
def phase4_compile_save() -> None:
    log.info("\n=== Phase 4: compile + save ===")
    out_v = call("validate_blueprint", {"asset_path": ASSET})
    log.info("  validate: %s", out_v)
    out_c = call("compile_blueprint", {"asset_path": ASSET})
    log.info("  compile:  %s", out_c)
    out_s = call("save_asset", {"asset_path": ASSET})
    log.info("  save:     %s", out_s)


def main() -> None:
    phase1_variable()
    p2 = phase2_update_variables()
    p3 = phase3_target_rotation()
    phase4_compile_save()
    log.info("\n[ALL DONE] phase2=%s phase3=%s", p2, p3)


if __name__ == "__main__":
    main()
