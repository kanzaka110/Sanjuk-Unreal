#!/usr/bin/env python3
"""ABRR Phase 0: ensure 5 missing variables for AnimRewindRecorderEmit graph.

Only adds variables that don't already exist. TrjPast/Current already exist.
"""
from __future__ import annotations

import json
import logging
import sys
import urllib.request
from typing import Any

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
ENDPOINT = "http://localhost:9316/mcp"

logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
log = logging.getLogger(__name__)

# Spec per Inspector handoff. Categories chosen per existing patterns:
#  - bAnimRewindRecording / RewindMonitorLine -> AnimRewind (memo: project_pc01_anim_rewind_recorder.md)
#  - bIsSprintEndTransition -> Buffer (memo: project_pc01_sprint_end_transition.md, sister to bIsSprintStartTransition)
#  - UpperBodyBlendWeight / CurrentSequenceName -> "디폴트" (matches TrjPastAngularVelocity/TrjCurrentAngularVelocity)
TARGET_VARS: list[dict[str, Any]] = [
    {
        "name": "bAnimRewindRecording",
        "type": "bool",
        "category": "AnimRewind",
        "default_value": "True",
        "instance_editable": True,
    },
    {
        "name": "RewindMonitorLine",
        "type": "text",
        "category": "AnimRewind",
    },
    {
        "name": "bIsSprintEndTransition",
        "type": "bool",
        "category": "Buffer",
        "default_value": "False",
    },
    {
        "name": "UpperBodyBlendWeight",
        "type": "float",
        "category": "디폴트",
        "default_value": "0.0",
    },
    {
        "name": "CurrentSequenceName",
        "type": "string",
        "category": "디폴트",
        "default_value": "",
    },
]


def rpc(action: str, params: dict[str, Any]) -> Any:
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "blueprint_query",
            "arguments": {"action": action, "params": params},
        },
    }
    req = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if data.get("result", {}).get("isError"):
        return {"_error": data["result"]["content"][0]["text"][:400]}
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except Exception:
        return txt


def current_var_set() -> set[str]:
    r = rpc("get_variables", {"asset_path": ASSET})
    if not r or (isinstance(r, dict) and "_error" in r):
        log.warning("get_variables failed; assuming empty")
        return set()
    vars_list = r.get("variables", []) if isinstance(r, dict) else []
    return {v.get("name") for v in vars_list if v.get("name")}


def add_variable(spec: dict[str, Any]) -> bool:
    params: dict[str, Any] = {
        "asset_path": ASSET,
        "name": spec["name"],
        "type": spec["type"],
    }
    if "default_value" in spec:
        params["default_value"] = spec["default_value"]
    if "category" in spec:
        params["category"] = spec["category"]
    for key in ("instance_editable", "blueprint_read_only", "expose_on_spawn",
                "replicated", "transient"):
        if key in spec:
            params[key] = spec[key]

    r = rpc("add_variable", params)
    if r is None:
        log.error("FAIL %s — no response", spec["name"])
        return False
    if isinstance(r, dict) and "_error" in r:
        log.error("FAIL %s — %s", spec["name"], r["_error"][:200])
        return False
    log.info("OK   %s (%s) cat=%s", spec["name"], spec["type"], spec.get("category"))
    return True


def main() -> None:
    existing = current_var_set()
    log.info("Existing variables: %d", len(existing))

    to_add = [v for v in TARGET_VARS if v["name"] not in existing]
    skipped = [v["name"] for v in TARGET_VARS if v["name"] in existing]

    log.info("Target: %d  to_add: %d  skipped(exists): %s",
             len(TARGET_VARS), len(to_add), skipped)

    fail = 0
    for spec in to_add:
        if not add_variable(spec):
            fail += 1

    if fail:
        log.error("=== Phase 0 FAILED: %d errors ===", fail)
        sys.exit(2)
    log.info("=== Phase 0 OK ===")


if __name__ == "__main__":
    main()
