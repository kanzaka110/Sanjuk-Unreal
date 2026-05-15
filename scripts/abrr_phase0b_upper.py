#!/usr/bin/env python3
"""Phase 0b retry: add UpperBodyBlendWeight only, with ASCII category."""
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


def main() -> None:
    spec = {
        "asset_path": ASSET,
        "name": "UpperBodyBlendWeight",
        "type": "float",
        "category": "Default",
        "default_value": "0.0",
    }
    print("Trying type=float ...")
    r = rpc("add_variable", spec)
    print("Response:", r if not isinstance(r, dict) or "_error" not in r else r["_error"][:600])

    # check existence
    g = rpc("get_variables", {"asset_path": ASSET})
    if isinstance(g, dict):
        found = [v for v in g.get("variables", []) if v.get("name") == "UpperBodyBlendWeight"]
        print("Existence after add:", bool(found), found[:1] if found else None)


if __name__ == "__main__":
    main()
