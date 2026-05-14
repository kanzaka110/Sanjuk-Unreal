#!/usr/bin/env python3
"""Restore PC_01_ABP variables from backup + add 5/14 chain variables.

Sources:
  - scripts/backup/Variables_pre_sprint_start_20260514.json  (130 vars, 5/14 pre)
  - Sprint Start chain 6 vars (5/14 신규, 백업 없음 — 코드에 명시)
  - Phase 3 게이트 변수 bIsPlayingTransitionBack (5/13)

Strategy:
  1) Dump current ABP variables (probe_abp_vars 패턴)
  2) Skip ones already present (by name)
  3) Add missing ones via Monolith blueprint_query::add_variable

Idempotent — 여러 번 돌려도 안전.

Usage:
  py C:/Dev/Sanjuk-Unreal/scripts/restore_abp_variables.py
  py C:/Dev/Sanjuk-Unreal/scripts/restore_abp_variables.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import urllib.request

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
ENDPOINT = "http://localhost:9316/mcp"
BACKUP_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "backup",
    "Variables_pre_sprint_start_20260514.json",
)

# 5/14 Sprint Start chain — 백업에 없음
SPRINT_START_VARS: list[dict] = [
    {"name": "bCurrentPendingSprinting",      "type": "bool",   "default_value": "False",     "category": "Buffer"},
    {"name": "bJustEnteredSprint",            "type": "bool",   "default_value": "False",     "category": "Buffer"},
    {"name": "SprintStartTransitionRemain",   "type": "double", "default_value": "0.0",       "category": "Buffer"},
    {"name": "SprintStartTransitionDuration", "type": "double", "default_value": "0.3",       "category": "Essential Values", "instance_editable": True},
    {"name": "bIsSprintStartTransition",      "type": "bool",   "default_value": "False",     "category": "Buffer"},
    {"name": "bPrevPendingSprinting",         "type": "bool",   "default_value": "False",     "category": "Buffer"},
]

# 5/13 Phase 3 게이트
PHASE3_VARS: list[dict] = [
    {"name": "bIsPlayingTransitionBack", "type": "bool", "default_value": "False", "category": "Buffer"},
]


logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
log = logging.getLogger(__name__)
_msg_id = [0]


def rpc(action: str, params: dict) -> dict | str | None:
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
        ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        log.error("RPC failed: %s", exc)
        return None
    if data.get("result", {}).get("isError"):
        return {"_error": data["result"]["content"][0]["text"][:400]}
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except Exception:
        return txt


def load_backup_vars() -> list[dict]:
    """Parse 130 vars from backup JSON."""
    with open(BACKUP_PATH, "r", encoding="utf-8") as f:
        outer = json.load(f)
    text = outer["result"]["content"][0]["text"]
    inner = json.loads(text)
    return inner.get("variables", [])


def get_current_vars() -> set[str]:
    """Dump current ABP variables. Returns set of names."""
    r = rpc("get_variables", {"asset_path": ASSET})
    if not r:
        log.warning("Could not dump current variables — assuming empty")
        return set()
    if isinstance(r, dict) and "_error" in r:
        log.warning("get_variables error: %s", r["_error"][:200])
        return set()
    vars_list = r.get("variables", []) if isinstance(r, dict) else []
    return {v.get("name") for v in vars_list if v.get("name")}


def add_variable(spec: dict, dry_run: bool = False) -> bool:
    """Add one variable to ABP."""
    params = {
        "asset_path": ASSET,
        "variable_name": spec["name"],
        "variable_type": spec["type"],
    }
    if "default_value" in spec:
        params["default_value"] = spec["default_value"]
    if "category" in spec:
        params["category"] = spec["category"]
    for key in ("instance_editable", "blueprint_read_only", "expose_on_spawn",
                "replicated", "transient"):
        if key in spec:
            params[key] = spec[key]

    if dry_run:
        log.info("  [DRY] add_variable %s (%s) cat=%s", spec["name"], spec["type"], spec.get("category", "?"))
        return True

    r = rpc("add_variable", params)
    if r is None:
        log.error("  FAIL %s — no response", spec["name"])
        return False
    if isinstance(r, dict) and "_error" in r:
        log.error("  FAIL %s — %s", spec["name"], r["_error"][:160])
        return False
    log.info("  OK   %s (%s)", spec["name"], spec["type"])
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print actions only, no API calls for add")
    args = parser.parse_args()

    log.info("=== Loading backup variables ===")
    backup_vars = load_backup_vars()
    log.info("Backup variables: %d", len(backup_vars))

    log.info("\n=== Dumping current ABP variables ===")
    current = get_current_vars()
    log.info("Currently present: %d", len(current))

    all_specs = backup_vars + SPRINT_START_VARS + PHASE3_VARS
    log.info("\n=== Total target variables: %d (backup=%d + sprint_start=%d + phase3=%d) ===",
             len(all_specs), len(backup_vars), len(SPRINT_START_VARS), len(PHASE3_VARS))

    to_add = [v for v in all_specs if v["name"] not in current]
    log.info("Missing (to add): %d", len(to_add))

    if not to_add:
        log.info("Nothing to do. All variables present.")
        return

    log.info("\n=== Adding %d variables ===", len(to_add))
    ok_count = 0
    fail_count = 0
    for spec in to_add:
        if add_variable(spec, dry_run=args.dry_run):
            ok_count += 1
        else:
            fail_count += 1

    log.info("\n=== Result: OK=%d FAIL=%d ===", ok_count, fail_count)
    if fail_count > 0:
        sys.exit(2)


if __name__ == "__main__":
    main()
