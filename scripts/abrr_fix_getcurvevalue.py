#!/usr/bin/env python3
"""Fix 4 GetCurveValue nodes that were created against SkeletalMeshComponent
instead of AnimInstance. Remove and recreate with target_class hint, then
re-wire to FormatText.

Affected (live IDs based on Phase3 log):
  CF_10 -> FT.eprw  (backup K2Node_CallFunction_18 GetCurveValue 'enable_playratewarping')
  CF_14 -> FT.phase (backup K2Node_CallFunction_46 GetCurveValue 'Phase')
  CF_15 -> FT.eow   (backup K2Node_CallFunction_48 GetCurveValue 'enable_orientationwarping')
  CF_21 -> FT.dal   (backup K2Node_CallFunction_121 GetCurveValue 'Disable_AdditiveLean')
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPH = "AnimRewindRecorderEmit"
ENDPOINT = "http://localhost:9316/mcp"
MAP_PATH = Path(r"C:\Dev\Sanjuk-Unreal\Saved\ABRR_id_map.json")

FT_LIVE = "K2Node_FormatText_1"

# Bad nodes: (live_id, position, curve_name, ft_pin)
BADS = [
    ("K2Node_CallFunction_10", [5104, 544], "enable_playratewarping", "eprw"),
    ("K2Node_CallFunction_14", [5104, 272], "Phase", "phase"),
    ("K2Node_CallFunction_15", [5104, 400], "enable_orientationwarping", "eow"),
    ("K2Node_CallFunction_21", [3776, 1584], "Disable_AdditiveLean", "dal"),
]


def rpc(action: str, params: dict) -> dict | str | None:
    body = {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "blueprint_query",
                   "arguments": {"action": action, "params": params}},
    }
    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    if data.get("result", {}).get("isError"):
        return {"_error": data["result"]["content"][0]["text"][:600]}
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except Exception:
        return txt


def main() -> None:
    id_map: dict[str, str] = json.loads(MAP_PATH.read_text(encoding="utf-8-sig"))
    rev: dict[str, str] = {v: k for k, v in id_map.items()}

    for live_id, pos, curve, ft_pin in BADS:
        old_id = rev.get(live_id, "?")
        print(f"\n--- {live_id} (old={old_id}) curve={curve!r} ---")

        # 1) remove
        r = rpc("remove_node", {"asset_path": ASSET, "graph_name": GRAPH, "node_id": live_id})
        print(f"  remove: {r}")

        # 2) add with target_class=AnimInstance
        for tc in ("AnimInstance", "SBActorAnimInstance"):
            r = rpc("add_node", {
                "asset_path": ASSET, "graph_name": GRAPH,
                "node_type": "function", "function_name": "GetCurveValue",
                "target_class": tc, "position": pos,
            })
            if isinstance(r, dict) and "_error" not in r:
                new_id = r.get("node_id") or r.get("id")
                print(f"  add(target_class={tc}): {new_id}")
                break
            print(f"  add(target_class={tc}) failed: {r.get('_error','')[:200] if isinstance(r,dict) else r}")
        else:
            print("  ALL add attempts failed")
            continue

        # 3) set CurveName default
        r = rpc("set_pin_default", {
            "asset_path": ASSET, "graph_name": GRAPH, "node_id": new_id,
            "pin_name": "CurveName", "value": curve,
        })
        print(f"  set CurveName={curve!r}: {r}")

        # 4) connect ReturnValue -> FT.ft_pin
        r = rpc("connect_pins", {
            "asset_path": ASSET, "graph_name": GRAPH,
            "source_node": new_id, "source_pin": "ReturnValue",
            "target_node": FT_LIVE, "target_pin": ft_pin,
        })
        print(f"  wire ReturnValue -> {FT_LIVE}.{ft_pin}: {r}")

        # 5) update id_map (replace mapping for old_id)
        if old_id != "?":
            id_map[old_id] = new_id

    MAP_PATH.write_text(json.dumps(id_map, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nUpdated ID map: {MAP_PATH}")


if __name__ == "__main__":
    main()
