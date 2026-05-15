#!/usr/bin/env python3
"""Phase 0c: try multiple variable_type spellings for UpperBodyBlendWeight.

Some Monolith builds need 'real:float' or 'real:double' for the actual
UE-side property type. Try variants and verify after each.
"""
from __future__ import annotations

import json
import urllib.request

ASSET = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
ENDPOINT = "http://localhost:9316/mcp"


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
        return {"_error": data["result"]["content"][0]["text"]}
    txt = data["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except Exception:
        return txt


def exists(name: str) -> bool:
    g = rpc("get_variables", {"asset_path": ASSET})
    if isinstance(g, dict):
        return any(v.get("name") == name for v in g.get("variables", []))
    return False


def attempt(var_type: str, label: str) -> bool:
    if exists("UpperBodyBlendWeight"):
        print(f"Already exists -- skipping {label}")
        return True
    spec = {
        "asset_path": ASSET,
        "name": "UpperBodyBlendWeight",
        "type": var_type,
        "default_value": "0.0",
        "category": "Debug",
    }
    print(f"[{label}] add_variable type={var_type!r}")
    r = rpc("add_variable", spec)
    if isinstance(r, dict) and "_error" in r:
        print("  err:", r["_error"][:300])
        return False
    print("  resp:", r)
    found = exists("UpperBodyBlendWeight")
    print("  exists after:", found)
    return found


def main() -> None:
    candidates = [
        ("real:float", "Variant A"),
        ("double", "Variant B"),
        ("real:double", "Variant C"),
        ("Real (single-precision)", "Variant D"),
    ]
    for vt, label in candidates:
        if attempt(vt, label):
            print("SUCCESS with", vt)
            return
    print("All variants failed.")


if __name__ == "__main__":
    main()
