#!/usr/bin/env python3
"""
PC_01_ABP — CurrentSequenceName stale 처방: EventGraph 의 BlueprintUpdateAnimation
event 에서 매 틱 game thread 시점에 set (2026-05-15).

문제: CurrentSequenceName 가 DrawDebug 그래프 (PostEvaluateAnimation 시점) 에서만 set.
PostEvaluate 는 BPThreadSafeUpdateAnimation (UpdateVariables 호출 시점) 다음 시점이라
UpdateVariables 가 읽을 때 1프레임 lag 또는 조건부 (BooleanAND_19) false 시 영원히 stale.

처방: EventGraph 에 BlueprintUpdateAnimation event 신규 추가 → game thread 매 틱 시점.
NativeUpdateAnimation 다음, BPThreadSafeUpdateAnimation 직전 호출. 그 안에서:
    BlendStackInputs → BreakStruct → Anim → GetDisplayName → Set CurrentSequenceName
UpdateVariables (BPThreadSafe) 가 fresh 값 읽음.

이미 추가됨: K2Node_Event_0 (BlueprintUpdateAnimation, EventGraph)

남은 작업:
1. Get BlendStackInputs
2. BreakStruct (S_BlendStackInputs)
3. GetDisplayName (KismetSystemLibrary)
4. Set CurrentSequenceName
5. exec chain: K2Node_Event_0.then → SetCurrentSequenceName.execute
6. data wiring
7. compile + save
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("fix_csn_eventgraph")

ASSET = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
URL = "http://localhost:9316/mcp"
GRAPH = "EventGraph"
EVENT_NODE = "K2Node_Event_0"
_msg_id = [12000]


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
    label = kwargs.get("function_name") or kwargs.get("variable_name") or kwargs.get("struct_type") or node_type
    log.info("[+] %s -> %s", label, nid)
    return nid


def connect(src: str, src_pin: str, tgt: str, tgt_pin: str) -> Any:
    return call("connect_pins", {
        "asset_path": ASSET, "graph_name": GRAPH,
        "source_node": src, "source_pin": src_pin,
        "target_node": tgt, "target_pin": tgt_pin,
    })


def main() -> None:
    log.info("\n=== Step 1: data + exec nodes ===")
    get_bsi = add_node("VariableGet", [400, 500], variable_name="BlendStackInputs")
    bs = add_node("BreakStruct", [550, 540], struct_type="S_BlendStackInputs")
    get_disp = add_node("CallFunction", [800, 540],
                        function_name="GetDisplayName", target_class="KismetSystemLibrary")
    set_csn = add_node("VariableSet", [1000, 500], variable_name="CurrentSequenceName")

    log.info("\n=== Step 2: get BreakStruct Anim pin ===")
    bs_details = call("get_node_details", {"asset_path": ASSET, "graph_name": GRAPH, "node_id": bs})
    anim_pin = None
    for p in bs_details.get('pins', []):
        if 'Anim' in p.get('name','') and p.get('direction')=='output':
            anim_pin = p['name']
            break
    log.info("Anim pin = %s", anim_pin)

    log.info("\n=== Step 3: wiring ===")
    # exec: Event.then -> SetCurrentSequenceName.execute
    connect(EVENT_NODE, "then", set_csn, "execute")
    # data: BSI → BreakStruct.S_BlendStackInputs
    connect(get_bsi, "BlendStackInputs", bs, "S_BlendStackInputs")
    # BreakStruct.Anim → GetDisplayName.Object
    connect(bs, anim_pin, get_disp, "Object")
    # GetDisplayName.ReturnValue → SetCurrentSequenceName.CurrentSequenceName
    connect(get_disp, "ReturnValue", set_csn, "CurrentSequenceName")

    log.info("\n=== Step 4: compile + save ===")
    c = call("compile_blueprint", {"asset_path": ASSET})
    log.info("compile: %s", c)
    s = call("save_asset", {"asset_path": ASSET}, allow_error=True)
    log.info("save:    %s", s)


if __name__ == "__main__":
    main()
