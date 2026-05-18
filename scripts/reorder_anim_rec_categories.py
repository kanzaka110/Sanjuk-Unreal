#!/usr/bin/env python3
"""ANIM_REC 신13필드 chain 을 카테고리 순서로 재배치.

기존: fpa → ow_a → ps_db → ptrd → tta → hed → sv → ise → setr → seta → pas → pms2 → ppwm
신규: pas → pms2 → ppwm → ise → setr → seta → fpa → ow_a → ps_db → tta → ptrd → sv → hed

카테고리 매핑 (FT_2~FT_11 규격):
    State Prev   (FT_2 그룹): pas / pms2 / ppwm
    State Sprint (FT_2 그룹): ise / setr / seta
    IK           (FT_3 그룹): fpa / ow_a
    Clip / MM DB (FT_4 그룹): ps_db
    Motion / 회전(FT_5/6 그룹): tta / ptrd / sv / hed

ABP 그래프상 노드 추가/삭제 없음 — wire 8개만 재배치.
save 호출 안 함 — compile 만, 사용자 Ctrl+S.
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("reorder")

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"
GRAPH = "AnimRewindRecorderEmit"

_msg_id = [19000]


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
        if allow_error:
            return None
        log.error("[ERR] %s -> %s", action, str(data)[:300])
        sys.exit(1)
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return txt


def disconnect(src: str, src_pin: str, tgt: str, tgt_pin: str) -> None:
    call("disconnect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "node_id": src, "pin_name": src_pin,
        "target_node": tgt, "target_pin": tgt_pin,
    }, allow_error=True)


def connect(src: str, src_pin: str, tgt: str, tgt_pin: str) -> None:
    call("connect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "source_node": src, "source_pin": src_pin,
        "target_node": tgt, "target_pin": tgt_pin,
    })


# (src, src_pin, old_target, old_pin, new_target, new_pin) — 6 wire 만 실제 변경
# 기존: chain wires that need rerouting (출발 노드 동일, 도착 노드만 변경)
WIRES = [
    # CF_15.Result → CF_93.A  (FT_11 t2s 뒤 → pas 시작)
    ("K2Node_CallFunction_15", "ReturnValue", "K2Node_CallFunction_23", "A", "K2Node_CallFunction_93", "A"),
    # CF_91.Result → CF_23.A  (seta 뒤 → fpa 시작)
    ("K2Node_CallFunction_91", "ReturnValue", "K2Node_CallFunction_93", "A", "K2Node_CallFunction_23", "A"),
    # CF_100.Result → CF_84.A (ppwm 뒤 → ise 시작)
    ("K2Node_CallFunction_100", "ReturnValue", "K2Node_CallFunction_25", "InString",
     "K2Node_CallFunction_84", "A"),
    # CF_40.Result → CF_67.A  (ps_db 뒤 → tta 시작)
    ("K2Node_CallFunction_40", "ReturnValue", "K2Node_CallFunction_61", "A", "K2Node_CallFunction_67", "A"),
    # CF_69.Result → CF_61.A  (tta 뒤 → ptrd 시작)
    ("K2Node_CallFunction_69", "ReturnValue", "K2Node_CallFunction_73", "A", "K2Node_CallFunction_61", "A"),
    # CF_63.Result → CF_79.A  (ptrd 뒤 → sv 시작)
    ("K2Node_CallFunction_63", "ReturnValue", "K2Node_CallFunction_67", "A", "K2Node_CallFunction_79", "A"),
    # CF_81.Result → CF_73.A  (sv 뒤 → hed 시작)
    ("K2Node_CallFunction_81", "ReturnValue", "K2Node_CallFunction_84", "A", "K2Node_CallFunction_73", "A"),
    # CF_75.Result → CF_25.InString  (hed 뒤 → 최종 StringToText)
    ("K2Node_CallFunction_75", "ReturnValue", "K2Node_CallFunction_79", "A",
     "K2Node_CallFunction_25", "InString"),
]


def main() -> None:
    log.info("\n=== ANIM_REC chain 카테고리 순서 재배치 ===")
    log.info("    (State Prev → State Sprint → IK → Clip → Motion)")

    for i, (src, src_pin, old_tgt, old_pin, new_tgt, new_pin) in enumerate(WIRES, 1):
        log.info("\n--- [%d/%d] %s.%s ---", i, len(WIRES), src, src_pin)
        log.info("  disconnect %s.%s → %s.%s", src, src_pin, old_tgt, old_pin)
        disconnect(src, src_pin, old_tgt, old_pin)
        log.info("  connect    %s.%s → %s.%s", src, src_pin, new_tgt, new_pin)
        connect(src, src_pin, new_tgt, new_pin)

    log.info("\n=== compile (save 생략 — Ctrl+S 수동) ===")
    c = call("compile_blueprint", {"asset_path": ASSET})
    log.info("compile: success=%s errors=%s warnings=%s",
             c.get("success"), c.get("error_count"), c.get("warning_count"))
    if c.get("errors"):
        for e in c["errors"][:5]:
            log.error("  ! %s", e)
    log.info("\n>>> SB2 에디터에서 PC_01_ABP 탭 → Ctrl+S 로 저장해주세요.")


if __name__ == "__main__":
    main()
