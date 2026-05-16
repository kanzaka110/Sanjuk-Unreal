"""Monolith MCP RPC 표준 클라이언트.

기존 step1~6, restore_*, build_*, dump_* 들이 각자 rpc() 함수를 갖고 있던 걸
이 모듈로 통일. retry / dry-run / silent / endpoint override 지원.

환경변수:
  MONOLITH_ENDPOINT (default: http://localhost:9316/mcp)
  MONOLITH_TIMEOUT  (default: 60)
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from typing import Any

DEFAULT_ENDPOINT = os.environ.get("MONOLITH_ENDPOINT", "http://localhost:9316/mcp")
DEFAULT_TIMEOUT = int(os.environ.get("MONOLITH_TIMEOUT", "60"))

_msg_id = [0]


def rpc(
    tool_name: str,
    action: str,
    params: dict | None = None,
    *,
    endpoint: str | None = None,
    timeout: int | None = None,
    retries: int = 3,
    silent: bool = False,
) -> dict | str | None:
    """Standard wrapper for `tools/call` MCP method.

    Args:
        tool_name: e.g. "blueprint_query", "animation_query"
        action:    e.g. "add_node", "compile_blueprint"
        params:    action-specific arguments
        retries:   how many times to retry on transport error
        silent:    suppress error stderr prints (for fallback patterns)

    Returns:
        - parsed JSON dict / str on success
        - {"_error": "<msg>"} on Monolith-side error (isError=True)
        - None on transport failure after retries
    """
    _msg_id[0] += 1
    body = {
        "jsonrpc": "2.0",
        "id": _msg_id[0],
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": {"action": action, "params": params or {}},
        },
    }
    ep = endpoint or DEFAULT_ENDPOINT
    to = timeout or DEFAULT_TIMEOUT

    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                ep,
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=to) as resp:
                raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            if data.get("result", {}).get("isError"):
                msg = data["result"]["content"][0]["text"]
                if not silent:
                    print(f"!! {tool_name}::{action} ERROR: {msg[:300]}", file=sys.stderr)
                return {"_error": msg}
            txt = data["result"]["content"][0]["text"]
            try:
                return json.loads(txt)
            except Exception:
                return txt
        except Exception as exc:
            last_exc = exc
            if attempt < retries - 1:
                time.sleep(0.5 * (attempt + 1))
                continue
    if not silent:
        print(f"!! {tool_name}::{action} TRANSPORT FAIL after {retries}: {last_exc}", file=sys.stderr)
    return None


# Convenience wrappers per common tool
def call_blueprint(action: str, params: dict | None = None, **kw) -> Any:
    return rpc("blueprint_query", action, params, **kw)


def call_animation(action: str, params: dict | None = None, **kw) -> Any:
    return rpc("animation_query", action, params, **kw)


def call_chooser(action: str, params: dict | None = None, **kw) -> Any:
    """May not exist yet — fallback to blueprint_query if so."""
    r = rpc("chooser_query", action, params, silent=True, **kw)
    if r is None or (isinstance(r, dict) and "_error" in r):
        # fallback try blueprint_query
        return rpc("blueprint_query", action, params, **kw)
    return r


def compile_and_save(asset_path: str) -> tuple[bool, dict]:
    """Compile + save blueprint. Returns (ok, info)."""
    c = call_blueprint("compile_blueprint", {"asset_path": asset_path})
    if not c or (isinstance(c, dict) and "_error" in c):
        return False, c or {}
    if isinstance(c, dict) and c.get("error_count", 0) > 0:
        return False, c
    s = call_blueprint("save_asset", {"asset_path": asset_path})
    return True, {"compile": c, "save": s}
