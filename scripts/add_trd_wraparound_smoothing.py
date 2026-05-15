#!/usr/bin/env python3
"""
PC_01_ABP — UpdateTargetRotation Strafe 분기 trd wraparound 평활화 (회전 튐 처방 A).

진단 (2026-05-15 [ANIM_REC] 실측):
- f161-163: Sprint_Stop_F_Rfoot 중 trd 0 → 180 → -174 (sign 반전) 1프레임 jump
- f139-140: Sprint_Start 중 trd 42 → 80 (38° jump) → clip swap Sprint_Turn_R_090

원인: NormalizeAxis(Yaw * -1) 결과를 즉시 Set. 180° 경계 wraparound + 큰 step 변동
시 mesh가 visible jitter. BlendStack BlendTime=0.2 가 격변 따라가지 못함.

처방: 새 PrevTargetRotationDelta 변수 + shortest-arc delta + 0.5 lerp 평활화.

데이터 흐름 (Strafe 분기 한정):
    RawDelta = NormalizeAxis(NormalizedDeltaRotator.Yaw * -1)  // 기존 CF_4
    Diff = NormalizeAxis(RawDelta - PrevDelta)                  // shortest-arc 보장
    SmoothDelta = NormalizeAxis(PrevDelta + Diff * 0.5)         // 50% lerp + wrap
    TargetRotationDelta = SmoothDelta
    PrevTargetRotationDelta = SmoothDelta  // 다음 프레임용

exec chain (Strafe 분기):
    [Knot_1.OutputPin] → Set_3.execute (기존)
    Set_3.then → SetPrev.execute (신규)
    SetPrev.then → 끝
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("trd_smooth")

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"
PREV_VAR = "PrevTargetRotationDelta"
ALPHA = 0.5

_msg_id = [8000]


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


def add_node(graph: str, node_type: str, position: list[int], **kwargs: Any) -> str:
    out = call("add_node", {
        "asset_path": ASSET, "graph_name": graph,
        "node_type": node_type, "position": position, **kwargs,
    })
    nid = out["id"] if isinstance(out, dict) else out
    label = kwargs.get("function_name") or kwargs.get("variable_name") or node_type
    log.info("[+] %s %s -> %s", graph, label, nid)
    return nid


def connect(graph: str, src: str, src_pin: str, tgt: str, tgt_pin: str) -> Any:
    return call("connect_pins", {
        "asset_path": ASSET, "graph_name": graph,
        "source_node": src, "source_pin": src_pin,
        "target_node": tgt, "target_pin": tgt_pin,
    })


def disconnect(graph: str, src: str, src_pin: str, tgt: str, tgt_pin: str) -> Any:
    return call("disconnect_pins", {
        "asset_path": ASSET, "graph_name": graph,
        "node_id": src, "pin_name": src_pin,
        "target_node": tgt, "target_pin": tgt_pin,
    })


def set_pin(graph: str, node_id: str, pin_name: str, value: str) -> Any:
    return call("set_pin_default", {
        "asset_path": ASSET, "graph_name": graph,
        "node_id": node_id, "pin_name": pin_name, "value": value,
    })


# ---------------------------------------------------------------------------
# Phase 1: variable
# ---------------------------------------------------------------------------
def phase1_variable() -> None:
    log.info("\n=== Phase 1: PrevTargetRotationDelta 변수 ===")
    call("add_variable", {
        "asset_path": ASSET,
        "name": PREV_VAR,
        "type": "double",
        "category": "Buffer",
        "default_value": "0.0",
        "instance_editable": False,
        "blueprint_read_only": False,
    })


# ---------------------------------------------------------------------------
# Phase 2: smoothing nodes + rewire
# ---------------------------------------------------------------------------
def phase2_smoothing() -> dict[str, str]:
    log.info("\n=== Phase 2: smoothing nodes + rewire ===")
    graph = "UpdateTargetRotation"

    # 신규 노드 추가
    get_prev_a = add_node(graph, "VariableGet", [1900, 700], variable_name=PREV_VAR)
    get_prev_b = add_node(graph, "VariableGet", [2200, 800], variable_name=PREV_VAR)
    sub_diff = add_node(graph, "CallFunction", [2080, 700],
                        function_name="Subtract_DoubleDouble", target_class="KismetMathLibrary")
    na1 = add_node(graph, "CallFunction", [2240, 700],
                   function_name="NormalizeAxis", target_class="KismetMathLibrary")
    mul_half = add_node(graph, "CallFunction", [2400, 700],
                        function_name="Multiply_DoubleDouble", target_class="KismetMathLibrary")
    add_smooth = add_node(graph, "CallFunction", [2560, 700],
                          function_name="Add_DoubleDouble", target_class="KismetMathLibrary")
    na2 = add_node(graph, "CallFunction", [2720, 700],
                   function_name="NormalizeAxis", target_class="KismetMathLibrary")
    set_prev = add_node(graph, "VariableSet", [2920, 720], variable_name=PREV_VAR)

    # 데이터 wiring
    # RawDelta - PrevDelta
    connect(graph, "K2Node_CallFunction_4", "ReturnValue", sub_diff, "A")
    connect(graph, get_prev_a, PREV_VAR, sub_diff, "B")
    # NormalizeAxis(diff) → na1
    connect(graph, sub_diff, "ReturnValue", na1, "Angle")
    # na1 * 0.5
    connect(graph, na1, "ReturnValue", mul_half, "A")
    set_pin(graph, mul_half, "B", "0.5")
    # PrevDelta + mul_half
    connect(graph, get_prev_b, PREV_VAR, add_smooth, "A")
    connect(graph, mul_half, "ReturnValue", add_smooth, "B")
    # NormalizeAxis(add_smooth) → na2 (= SmoothDelta)
    connect(graph, add_smooth, "ReturnValue", na2, "Angle")

    # 기존 wiring 교체: CF_4 → Set_3 끊고, na2 → Set_3
    disconnect(graph, "K2Node_CallFunction_4", "ReturnValue",
               "K2Node_VariableSet_3", "TargetRotationDelta")
    connect(graph, na2, "ReturnValue", "K2Node_VariableSet_3", "TargetRotationDelta")

    # SetPrev.input ← na2 (data)
    connect(graph, na2, "ReturnValue", set_prev, PREV_VAR)

    # exec: Set_3.then → SetPrev.execute
    connect(graph, "K2Node_VariableSet_3", "then", set_prev, "execute")

    log.info("[OK] Phase 2 done. set_prev=%s na2=%s", set_prev, na2)
    return {
        "get_prev_a": get_prev_a, "get_prev_b": get_prev_b,
        "sub_diff": sub_diff, "na1": na1, "mul_half": mul_half,
        "add_smooth": add_smooth, "na2": na2, "set_prev": set_prev,
    }


# ---------------------------------------------------------------------------
# Phase 3: compile + save
# ---------------------------------------------------------------------------
def phase3_compile_save() -> None:
    log.info("\n=== Phase 3: compile + save ===")
    out_c = call("compile_blueprint", {"asset_path": ASSET})
    log.info("  compile: %s", out_c)
    out_s = call("save_asset", {"asset_path": ASSET}, allow_error=True)
    log.info("  save:    %s", out_s)


def main() -> None:
    phase1_variable()
    p2 = phase2_smoothing()
    phase3_compile_save()
    log.info("\n[ALL DONE] %s", p2)


if __name__ == "__main__":
    main()
