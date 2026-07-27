# 손별 창 상대 램프 사전 프로브 (2026-07-25)
# 1) 변수 존재: LedgeProcWinL/R, LedgeSlopeMoveFloor, (신설 예정) LedgeProcRampL/R
# 2) Ledge_ProcWindow 그래프: prog/sel/branch 노드 ID + 창 상수 확인
# 3) Ledge_HandAlpha: FMax(MoveFloor 배관) + ProcWin 곱 노드 확인
import json
import urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"


def call(tool: str, action: str, params: dict, timeout: int = 300) -> dict:
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:400])
    return json.loads(txt)


def bq(action: str, params: dict) -> dict:
    p = {"asset_path": ABP}
    p.update(params)
    return call("blueprint_query", action, p)


def dump_graph(graph_name: str) -> dict:
    return {n["id"]: n for n in bq("get_graph_data", {"graph_name": graph_name})["nodes"]}


def pin_map(node: dict) -> dict:
    return {p["name"]: p for p in node.get("pins", [])}


def brief(node: dict) -> str:
    fn = node.get("function_name") or node.get("member_name") or ""
    var = node.get("variable_name") or ""
    return f'{node["class"].split(".")[-1]} {fn}{var}'


# ── 1) 변수 ──
var_names = {v["name"] for v in bq("get_variables", {}).get("variables", [])}
for v in ("LedgeProcWinL", "LedgeProcWinR", "LedgeSlopeMoveFloor",
          "LedgeProcRampL", "LedgeProcRampR"):
    print("[VAR]", v, "O" if v in var_names else "X")

# ── 2) Ledge_ProcWindow ──
pw = dump_graph("Ledge_ProcWindow")
print("\n[PW] nodes:", len(pw))
for nid, n in pw.items():
    pm = pin_map(n)
    tags = []
    for pname, p in pm.items():
        dv = p.get("default_value")
        if dv not in (None, "", "0.0") and p.get("direction") == "input":
            tags.append(f"{pname}={dv}")
    links = []
    for pname, p in pm.items():
        for c in p.get("connected_to", []) or []:
            links.append(f"{pname}->{c}")
    print(f"  {nid} | {brief(n)} | {' '.join(tags)}")
    for l in links:
        print(f"      {l}")

# ── 3) Ledge_HandAlpha — 전체 덤프 (function_name 필드 부재 → 핀으로 식별) ──
ha = dump_graph("Ledge_HandAlpha")
print("\n[HA] nodes:", len(ha))
for nid, n in ha.items():
    pm = pin_map(n)
    tags = []
    for pname, p in pm.items():
        dv = p.get("default_value")
        if dv not in (None, "", "0.0") and p.get("direction") == "input":
            tags.append(f"{pname}={dv}")
    print(f"  {nid} | {brief(n)} | {' '.join(tags)}")
    for pname, p in pm.items():
        for c in p.get("connected_to", []) or []:
            print(f"      {pname}->{c}")
