# -*- coding: utf-8 -*-
"""Monolith HTTP 호출 공용 헬퍼 (wall-hand DT화 작업)."""
import json, subprocess, sys

MCP = "http://localhost:9316/mcp"

def call(tool, args, timeout=60):
    p = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
         "params": {"name": tool, "arguments": args}}
    r = subprocess.run(
        ["curl", "-s", "-m", str(timeout), "-X", "POST", MCP,
         "-H", "Content-Type: application/json", "-d", json.dumps(p)],
        capture_output=True, text=True, timeout=timeout + 10)
    try:
        d = json.loads(r.stdout)
        c = d["result"]["content"][0]["text"]
        return d["result"].get("isError", False), c
    except Exception as e:
        return True, f"PARSE_FAIL {e}: {r.stdout[:500]}"

def bp(action, **kw):
    return call("blueprint_query", {"action": action, **kw})

if __name__ == "__main__":
    err, out = call(sys.argv[1], json.loads(sys.argv[2]))
    print("ERR" if err else "OK", out[:2000])
