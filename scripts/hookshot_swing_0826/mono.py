import json, urllib.request, sys

URL = "http://127.0.0.1:9316/mcp"

def call(tool, action, params=None, timeout=120):
    payload = {"jsonrpc":"2.0","id":1,"method":"tools/call",
               "params":{"name":tool,"arguments":{"action":action,"params":params or {}}}}
    req = urllib.request.Request(URL, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8")
    try:
        j = json.loads(raw)
    except Exception:
        return {"_raw": raw}
    try:
        txt = j["result"]["content"][0]["text"]
    except Exception:
        return j
    try:
        return json.loads(txt)
    except Exception:
        return {"_text": txt}

def p(o):
    print(json.dumps(o, ensure_ascii=False, indent=1)[:20000])
