#!/usr/bin/env python3
"""
PC_01_ABP — bIsPlayingTransitionBack 정확도 처방 (2026-05-15).

문제: CurrentSequenceName 변수가 DrawDebug 그래프 (PostEvaluateAnimation 시점) 에서만
set되어 UpdateVariables (BlueprintThreadSafeUpdateAnimation 시점) 가 읽을 때 stale.
+ DrawDebug 자체가 조건부 (BooleanAND_19) 라 false면 영원히 stale.

처방: UpdateVariables 안에서 직접 BlendStackInputs (struct) → BreakStruct → Anim_3 →
GetDisplayName → ClipName 으로 현재 클립명 추출. Contains 입력을 GetDisplayName.ReturnValue
로 교체. DrawDebug 의존성 완전 제거.

이미 추가됨: K2Node_BreakStruct_0 (struct_type=S_BlendStackInputs, Anim 핀 추출됨)

남은 작업:
1. Get BlendStackInputs 노드 추가
2. BlendStackInputs → BreakStruct_0.S_BlendStackInputs
3. GetDisplayName 노드 추가 (KismetSystemLibrary)
4. BreakStruct_0.Anim_3_* → GetDisplayName.Object
5. GetDisplayName.ReturnValue → Contains_37/38/39.SearchIn (3 wire)
6. 기존 VariableGet_52 → Contains 입력 disconnect (3 wire)
7. compile + save
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("fix_seqname")

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"
GRAPH = "UpdateVariables"
ANIM_PIN = "Anim_3_CE8F6C8948855759C43A24A538203DDC"

_msg_id = [11000]


def call(action: str, params: dict[str, Any], allow_error: bool = False) -> Any:
    _msg_id[0] += 1
    body = {
        "jsonrpc": "2.0", "id": _msg_id[0], "method": "tools/call",
        "params": {"name": "blueprint_query", "arguments": {"action": action, "params": params}},
    }
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8")
    data = json.loads(raw)
    if data.get("result", {}).get("isError"):
        if allow_error:
            log.warning("[WARN] action=%s err=%s", action, raw[:200])
            return None
        log.error("[ERROR] action=%s -> %s", action, raw[:400])
        sys.exit(1)
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return txt


def add_node(node_type: str, position: list[int], **kwargs: Any) -> str:
    out = call("add_node", {
        "asset_path": ASSET, "graph_name": GRAPH, "node_type": node_type,
        "position": position, **kwargs,
    })
    nid = out["id"] if isinstance(out, dict) else out
    label = kwargs.get("function_name") or kwargs.get("variable_name") or node_type
    log.info("[+] %s -> %s", label, nid)
    return nid


def connect(src: str, src_pin: str, tgt: str, tgt_pin: str) -> Any:
    return call("connect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "source_node": src, "source_pin": src_pin,
        "target_node": tgt, "target_pin": tgt_pin,
    })


def disconnect(src: str, src_pin: str, tgt: str, tgt_pin: str) -> Any:
    return call("disconnect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "node_id": src, "pin_name": src_pin,
        "target_node": tgt, "target_pin": tgt_pin,
    }, allow_error=True)


def main() -> None:
    log.info("\n=== Step 1: Get BlendStackInputs + GetDisplayName nodes ===")
    get_bsi = add_node("VariableGet", [6050, 2700], variable_name="BlendStackInputs")
    get_disp = add_node("CallFunction", [6450, 2700],
                        function_name="GetDisplayName", target_class="KismetSystemLibrary")

    log.info("\n=== Step 2: data wiring (BSI → BreakStruct → GetDisplayName) ===")
    connect(get_bsi, "BlendStackInputs", "K2Node_BreakStruct_0", "S_BlendStackInputs")
    connect("K2Node_BreakStruct_0", ANIM_PIN, get_disp, "Object")

    log.info("\n=== Step 3: replace Contains.SearchIn (CurrentSequenceName → GetDisplayName) ===")
    for cf in ["K2Node_CallFunction_37", "K2Node_CallFunction_38", "K2Node_CallFunction_39"]:
        disconnect("K2Node_VariableGet_52", "CurrentSequenceName", cf, "SearchIn")
        connect(get_disp, "ReturnValue", cf, "SearchIn")

    log.info("\n=== Step 4: compile + save ===")
    c = call("compile_blueprint", {"asset_path": ASSET})
    log.info("compile: %s", c)
    s = call("save_asset", {"asset_path": ASSET}, allow_error=True)
    log.info("save:    %s", s)


if __name__ == "__main__":
    main()
