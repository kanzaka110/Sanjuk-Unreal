#!/usr/bin/env python3
"""HasEvade 게이트 + InterpolationSettingsEvade 변수 추가.

회피 시 FootPlacement 의 Unplant Stiffness 강화 → 다리 빠르게 따라옴.

설계:
    GetFootPlacementInterpolationSettings 함수 시작:
        FunctionEntry → Branch_New (HasEvade)
            True  → Get InterpolationSettingsEvade → FunctionResult_New
            False → IfThenElse_2 (기존 흐름)

기존 wire: FunctionEntry.then → IfThenElse_2.execute  를 끊고 위 구조로.
save 호출 안 함 — compile 만.
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("evade_interp")

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"
GRAPH = "GetFootPlacementInterpolationSettings"

_msg_id = [23000]


def call(action: str, params: dict[str, Any], allow_error: bool = False) -> Any:
    _msg_id[0] += 1
    body = {
        "jsonrpc": "2.0", "id": _msg_id[0], "method": "tools/call",
        "params": {"name": "blueprint_query", "arguments": {"action": action, "params": params}},
    }
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    if data.get("result", {}).get("isError"):
        if allow_error: return None
        log.error("[ERR] %s -> %s", action, str(data)[:300])
        sys.exit(1)
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return txt


# 회피 전용 default — 보수적 시작 (UnplantLinearStiffness 4배 대신 2.4배)
EVADE_DEFAULT = (
    "(UnplantLinearStiffness=600.000000,UnplantLinearDamping=0.500000,"
    "UnplantAngularStiffness=700.000000,UnplantAngularDamping=1.000000,"
    "SeparationStiffness=1000.000000,SeparationDamping=1.000000,"
    "FloorLinearStiffness=1000.000000,FloorLinearDamping=1.000000,"
    "FloorAngularStiffness=450.000000,FloorAngularDamping=1.000000,"
    "bEnableFloorInterpolation=True,bSmoothRootBone=True,"
    "bEnableSeparationInterpolation=True)"
)


def main() -> None:
    log.info("\n=== Step 1: InterpolationSettingsEvade 변수 추가 ===")
    r = call("add_variable", {
        "asset_path": ASSET,
        "name": "InterpolationSettingsEvade",
        "type": "struct:FootPlacementInterpolationSettings",
        "default_value": EVADE_DEFAULT,
    }, allow_error=True)
    log.info("  %s", r)

    log.info("\n=== Step 2: Branch + Get + FunctionResult 노드 추가 ===")
    # Position 좌표는 기존 FunctionEntry 옆에 배치
    branch = call("add_node", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "node_type": "Branch", "position": [200, 0],
    })["id"]
    log.info("  Branch -> %s", branch)

    vget_evade = call("add_node", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "node_type": "VariableGet", "variable_name": "InterpolationSettingsEvade",
        "position": [400, 100],
    })["id"]
    log.info("  Get InterpolationSettingsEvade -> %s", vget_evade)

    vget_he = call("add_node", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "node_type": "VariableGet", "variable_name": "HasEvade",
        "position": [-100, 100],
    })["id"]
    log.info("  Get HasEvade -> %s", vget_he)

    # 새 FunctionResult — 회피 분기 반환
    fret_evade = call("add_node", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "node_type": "FunctionResult", "position": [800, 0],
    })["id"]
    log.info("  FunctionResult (Evade) -> %s", fret_evade)

    log.info("\n=== Step 3: Wire 연결 ===")
    # 1) 기존 wire 끊기: FunctionEntry.then → IfThenElse_2.execute
    r = call("disconnect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "node_id": "K2Node_FunctionEntry_0", "pin_name": "then",
        "target_node": "K2Node_IfThenElse_2", "target_pin": "execute",
    }, allow_error=True)
    log.info("  disconnect FunctionEntry → IfThenElse_2: %s", "ok" if r else "fail")

    # 2) FunctionEntry.then → Branch.execute
    call("connect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "source_node": "K2Node_FunctionEntry_0", "source_pin": "then",
        "target_node": branch, "target_pin": "execute",
    })
    log.info("  connect FunctionEntry.then → Branch.execute")

    # 3) Branch.True → FunctionResult_Evade.execute
    call("connect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "source_node": branch, "source_pin": "then",
        "target_node": fret_evade, "target_pin": "execute",
    })
    log.info("  connect Branch.then(True) → FunctionResult_Evade.execute")

    # 4) Branch.False → IfThenElse_2.execute (기존 흐름)
    call("connect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "source_node": branch, "source_pin": "else",
        "target_node": "K2Node_IfThenElse_2", "target_pin": "execute",
    })
    log.info("  connect Branch.else(False) → IfThenElse_2.execute")

    # 5) HasEvade VariableGet → Branch.Condition
    call("connect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "source_node": vget_he, "source_pin": "HasEvade",
        "target_node": branch, "target_pin": "Condition",
    })
    log.info("  connect HasEvade → Branch.Condition")

    # 6) Get InterpolationSettingsEvade → FunctionResult_Evade.ReturnValue
    call("connect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "source_node": vget_evade, "source_pin": "InterpolationSettingsEvade",
        "target_node": fret_evade, "target_pin": "ReturnValue",
    })
    log.info("  connect Evade VarGet → FunctionResult_Evade.ReturnValue")

    log.info("\n=== Step 4: compile ===")
    c = call("compile_blueprint", {"asset_path": ASSET})
    log.info("  compile: success=%s errors=%s warnings=%s",
             c.get("success"), c.get("error_count"), c.get("warning_count"))
    if c.get("errors"):
        for e in c["errors"][:5]: log.error("  ! %s", e)


if __name__ == "__main__":
    main()
