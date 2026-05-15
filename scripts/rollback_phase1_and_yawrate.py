#!/usr/bin/env python3
"""
PC_01_ABP — 2026-05-15 두 변경 통째 롤백.

사용자 호소: "노이즈가 훨씬 심해졌는데???"

Rollback targets:
1. PoseSearchData_Moving default — MaxControllerYawRate / RotateTowardsMovementSpeed
   필드 제거하여 원래 (SpeedRemappingCurve=..., AccelerationRemappingCurve=...) 만
   남기기. YawRate=0 이 의도였을 가능성.
2. ① Transition gate 통째 — 변수 bIsPlayingTransitionBack + UpdateVariables 노드
   9개 (Get×1 + Contains×3 + OR×2 + Set + Knot×0 + ExecutionSeq.then_12 chain) +
   UpdateTargetRotation 게이트 3노드 (SelectFloat + Not + Get) 제거.
   UpdateTargetRotation 의 NormalizeAxis(CF_4) → Set TargetRotationDelta(Set_3)
   직결 복원.

Order:
- Step A: UpdateTargetRotation 원복 (NormalizeAxis 직결)
- Step B: UpdateTargetRotation gate 3노드 제거 (SelectFloat=CF_7, Not=CF_8, Get=VarGet_3)
- Step C: UpdateVariables exec chain 원상복구 (Set_69 → Knot_1 끊고 ExecutionSeq.then_12 → Knot_1 직결)
- Step D: UpdateVariables 신규 노드 8개 + Set_69 제거
- Step E: bIsPlayingTransitionBack 변수 제거
- Step F: PoseSearchData_Moving default 원상복구
- Step G: compile + save
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("rollback")

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"
VAR_NAME = "bIsPlayingTransitionBack"

# Node IDs created/used by extend_transition_back_gate(_continue).py
UV_NODES_TO_REMOVE = [
    "K2Node_VariableSet_69",   # Set bIsPlayingTransitionBack
    "K2Node_CallFunction_35",  # OR2 (after narrow)
    "K2Node_CallFunction_34",  # OR1
    "K2Node_CallFunction_28",  # Contains Sprint_to_Jog
    "K2Node_CallFunction_11",  # Contains Sprint_to_LockOn
    "K2Node_CallFunction_7",   # Contains Sprint_to_Battle
    "K2Node_VariableGet_9",    # Get CurrentSequenceName (added by us)
]
UTR_NODES_TO_REMOVE = [
    "K2Node_CallFunction_7",   # SelectFloat (UpdateTargetRotation)
    "K2Node_CallFunction_8",   # Not_PreBool
    "K2Node_VariableGet_3",    # Get bIsPlayingTransitionBack
]
ORIGINAL_MOVING_DEFAULT = (
    "(SpeedRemappingCurve=(EditorCurveData=(DefaultValue=340282346638528859811704183484516925440.000000,"
    "PreInfinityExtrap=RCCE_Constant,PostInfinityExtrap=RCCE_Constant)),"
    "AccelerationRemappingCurve=(EditorCurveData=(DefaultValue=340282346638528859811704183484516925440.000000,"
    "PreInfinityExtrap=RCCE_Constant,PostInfinityExtrap=RCCE_Constant)))"
)

_msg_id = [7000]


def call(action: str, params: dict[str, Any], allow_error: bool = False) -> Any:
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
        if allow_error:
            log.warning("[WARN] action=%s err=%s", action, raw[:200])
            return None
        log.error("[ERROR] action=%s params=%s -> %s", action, params, raw)
        sys.exit(1)
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return txt


def step_a_restore_utr_wiring() -> None:
    log.info("\n=== Step A: UpdateTargetRotation NormalizeAxis 직결 복원 ===")
    graph = "UpdateTargetRotation"
    # SelectFloat.ReturnValue -X- Set_3.TargetRotationDelta
    call("disconnect_pins", {
        "asset_path": ASSET, "graph_name": graph,
        "node_id": "K2Node_CallFunction_7", "pin_name": "ReturnValue",
        "target_node": "K2Node_VariableSet_3", "target_pin": "TargetRotationDelta",
    }, allow_error=True)
    # NormalizeAxis(CF_4).ReturnValue → Set_3.TargetRotationDelta
    call("connect_pins", {
        "asset_path": ASSET, "graph_name": graph,
        "source_node": "K2Node_CallFunction_4", "source_pin": "ReturnValue",
        "target_node": "K2Node_VariableSet_3", "target_pin": "TargetRotationDelta",
    })
    log.info("  link: NormalizeAxis(CF_4).ReturnValue -> Set_3.TargetRotationDelta")


def step_b_remove_utr_nodes() -> None:
    log.info("\n=== Step B: UpdateTargetRotation gate 3노드 제거 ===")
    graph = "UpdateTargetRotation"
    for nid in UTR_NODES_TO_REMOVE:
        call("remove_node", {
            "asset_path": ASSET, "graph_name": graph, "node_id": nid,
        }, allow_error=True)
        log.info("  - removed %s", nid)


def step_c_restore_uv_exec() -> None:
    log.info("\n=== Step C: UpdateVariables exec chain 복원 ===")
    graph = "UpdateVariables"
    # Set_69.execute <- ExecutionSeq_3.then_12 → 끊기
    call("disconnect_pins", {
        "asset_path": ASSET, "graph_name": graph,
        "node_id": "K2Node_ExecutionSequence_3", "pin_name": "then_12",
        "target_node": "K2Node_VariableSet_69", "target_pin": "execute",
    }, allow_error=True)
    # Set_69.then → Knot_1.InputPin 끊기
    call("disconnect_pins", {
        "asset_path": ASSET, "graph_name": graph,
        "node_id": "K2Node_VariableSet_69", "pin_name": "then",
        "target_node": "K2Node_Knot_1", "target_pin": "InputPin",
    }, allow_error=True)
    # ExecutionSeq_3.then_12 → Knot_1.InputPin 직결 복원
    call("connect_pins", {
        "asset_path": ASSET, "graph_name": graph,
        "source_node": "K2Node_ExecutionSequence_3", "source_pin": "then_12",
        "target_node": "K2Node_Knot_1", "target_pin": "InputPin",
    })
    log.info("  link: ExecutionSeq_3.then_12 -> Knot_1.InputPin")


def step_d_remove_uv_nodes() -> None:
    log.info("\n=== Step D: UpdateVariables 신규 노드 7개 제거 ===")
    graph = "UpdateVariables"
    for nid in UV_NODES_TO_REMOVE:
        call("remove_node", {
            "asset_path": ASSET, "graph_name": graph, "node_id": nid,
        }, allow_error=True)
        log.info("  - removed %s", nid)


def step_e_remove_variable() -> None:
    log.info("\n=== Step E: bIsPlayingTransitionBack 변수 제거 ===")
    call("remove_variable", {
        "asset_path": ASSET,
        "name": VAR_NAME,
    })
    log.info("  - removed variable %s", VAR_NAME)


def step_f_restore_pose_search_default() -> None:
    log.info("\n=== Step F: PoseSearchData_Moving 디폴트 원상복구 ===")
    call("set_variable_defaults", {
        "asset_path": ASSET,
        "name": "PoseSearchData_Moving",
        "default_value": ORIGINAL_MOVING_DEFAULT,
    })
    log.info("  PoseSearchData_Moving 디폴트 원본 복구 (YawRate / RotateTowards 필드 제거)")


def step_g_compile_save() -> None:
    log.info("\n=== Step G: compile + save ===")
    out_c = call("compile_blueprint", {"asset_path": ASSET})
    log.info("  compile: %s", out_c)
    out_s = call("save_asset", {"asset_path": ASSET})
    log.info("  save:    %s", out_s)


def main() -> None:
    step_a_restore_utr_wiring()
    step_b_remove_utr_nodes()
    step_c_restore_uv_exec()
    step_d_remove_uv_nodes()
    step_e_remove_variable()
    step_f_restore_pose_search_default()
    step_g_compile_save()
    log.info("\n[ALL DONE]")


if __name__ == "__main__":
    main()
