#!/usr/bin/env python3
"""ANIM_REC dangling chain 정리 — 40 노드 일괄 삭제.

배경:
    add_anim_rec_10fields.py 가 첫 실행에서 부분 wire 실패 후 재실행되며 새 노드 시리즈
    추가. 결과: 신13필드 chain 이 ABP 안에 이중 존재 (Live + Dangling).

Live chain (유지): CF_15 → CF_23~CF_100 → CF_25 (PrintText 로 출력)
Dangling chain (삭제): CF_42~CF_82 시리즈 + Conv (CF_41/44/47/50/53/56/60/66/72/78)
                       + VariableGet (VG_52/53/54/55/56/57/59/61/63/65)

CF_40.ReturnValue → CF_42.A wire 끊고, 위 40 노드 삭제.
save 호출 안 함 — compile 만, 사용자 Ctrl+S.
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("cleanup")

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"
GRAPH = "AnimRewindRecorderEmit"

_msg_id = [21000]


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


# Dangling chain 노드 ID
DANGLING_CONCAT = [42, 43, 45, 46, 48, 49, 51, 52, 54, 55,
                   57, 58, 62, 64, 68, 70, 74, 76, 80, 82]
DANGLING_CONV = [41, 44, 47, 50, 53, 56, 60, 66, 72, 78]
DANGLING_VGET = [52, 53, 54, 55, 56, 57, 59, 61, 63, 65]


def main():
    log.info("\n=== Step 1: CF_40 → CF_42 분기 wire 끊기 ===")
    call("disconnect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "node_id": "K2Node_CallFunction_40", "pin_name": "ReturnValue",
        "target_node": "K2Node_CallFunction_42", "target_pin": "A",
    }, allow_error=True)
    log.info("  ok")

    log.info("\n=== Step 2: Dangling Concat 20 + Conv 10 노드 삭제 ===")
    for cid in DANGLING_CONCAT + DANGLING_CONV:
        nid = f"K2Node_CallFunction_{cid}"
        r = call("remove_node", {
            "asset_path": ASSET, "graph_name": GRAPH, "node_id": nid,
        }, allow_error=True)
        ok = bool(r and (isinstance(r, dict) and r.get("removed") or r is not None))
        log.info("  - %s : %s", nid, "removed" if r else "FAIL/skip")

    log.info("\n=== Step 3: Dangling VariableGet 10 노드 삭제 ===")
    for gid in DANGLING_VGET:
        nid = f"K2Node_VariableGet_{gid}"
        r = call("remove_node", {
            "asset_path": ASSET, "graph_name": GRAPH, "node_id": nid,
        }, allow_error=True)
        log.info("  - %s : %s", nid, "removed" if r else "FAIL/skip")

    log.info("\n=== compile ===")
    c = call("compile_blueprint", {"asset_path": ASSET})
    log.info("compile: success=%s errors=%s warnings=%s",
             c.get("success"), c.get("error_count"), c.get("warning_count"))
    if c.get("errors"):
        for e in c["errors"][:5]: log.error("  ! %s", e)

    # 검증
    log.info("\n=== 검증: CF_15 부터 chain trace ===")
    cur = "K2Node_CallFunction_15"
    visited = set()
    fields = []
    LIT_FIELD = {
        23: "fpa", 27: "ow_a", 34: "ps_db", 61: "ptrd", 67: "tta",
        73: "hed", 79: "sv", 84: "ise", 87: "setr", 90: "seta",
        93: "pas", 96: "pms2", 99: "ppwm",
    }
    while cur and cur not in visited and len(fields) < 20:
        visited.add(cur)
        d = call("get_node_details", {"asset_path":ASSET, "graph_name":GRAPH, "node_id":cur},
                 allow_error=True)
        if not d: break
        ret = []
        for p in d.get("pins", []):
            if p["name"] == "ReturnValue" and p.get("connected_to"):
                ret = p["connected_to"]
                break
        if not ret: break
        nxt = ret[0].split(".")[0]
        if nxt.startswith("K2Node_CallFunction_"):
            try:
                num = int(nxt.rsplit("_",1)[-1])
                if num in LIT_FIELD:
                    fields.append(LIT_FIELD[num])
            except ValueError: pass
        cur = nxt
    log.info("  Live chain 순서: %s", " → ".join(fields))


if __name__ == "__main__":
    main()
