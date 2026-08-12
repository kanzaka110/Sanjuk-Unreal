import json, urllib.request

URL = "http://127.0.0.1:9316/mcp"
_id = [0]

def call(tool, action, **params):
    _id[0] += 1
    payload = {"jsonrpc": "2.0", "id": _id[0], "method": "tools/call",
               "params": {"name": tool, "arguments": dict(action=action, **params)}}
    req = urllib.request.Request(URL, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        res = json.loads(r.read().decode("utf-8"))
    if "error" in res:
        raise RuntimeError(res["error"])
    txt = res["result"]["content"][0]["text"]
    try:
        return json.loads(txt)
    except Exception:
        return txt

def anim(action, **params):
    return call("animation_query", action, **params)
