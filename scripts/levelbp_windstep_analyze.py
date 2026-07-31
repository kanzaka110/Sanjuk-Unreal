# 레벨BP 분석 (read-only): 글로벌 윈드 스텝퍼 작업 전 현황 파악
#   1) BeginPlay exec 체인 순회 (타이틀/클래스)
#   2) K2Node_Literal ObjectRef 생존 여부 (맵 이동 후 경로)
#   3) Set WindStrength(SBWindVolume) 노드의 exec/값핀 배선
#   4) 글로벌 루프 Delay 의 Duration 소스
import json
import urllib.request

URL = "http://localhost:9316/mcp"
BP = "/Game/Developers/SHIFTUP/CSH/SB_Wind_TEST_Map/SBWind_Weight_TEST01_Map"
EG = "EventGraph"
OUT = {"chains": {}, "literals": [], "windstr_sets": [], "delays": [], "notes": []}


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


graphs = call("blueprint_query", "list_graphs", {"asset_path": BP})
OUT["graphs"] = [g["name"] for g in graphs.get("graphs", [])]

g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": EG})
nodes = {n["id"]: n for n in g["nodes"]}
OUT["node_count"] = len(nodes)


def pins_map(n: dict) -> dict:
    return {p["name"]: p for p in n.get("pins", [])}


def label(nid: str) -> str:
    n = nodes.get(nid, {})
    return "%s [%s] (%s)" % (n.get("title", "?"), n.get("class", "?").split(".")[-1], nid[:12])


# 1) 이벤트별 exec 체인 (BeginPlay / Tick)
for nid, n in nodes.items():
    t = n.get("title") or ""
    if "K2Node_Event" not in n.get("class", ""):
        continue
    if "BeginPlay" not in t.replace(" ", "") and "Tick" not in t:
        continue
    chain, visited, cur = [], set(), nid
    while cur and cur not in visited:
        visited.add(cur)
        chain.append(label(cur))
        nxt = None
        pm = pins_map(nodes[cur]) if cur in nodes else {}
        for pin_name, p in pm.items():
            if p.get("direction") != "output" or p.get("type") != "exec":
                continue
            ct = p.get("connected_to") or []
            if ct:
                nxt = ct[0].split(".")[0]
                chain[-1] += " --%s-->" % pin_name
                break
        if not nxt:
            break
        cur = nxt
        if len(chain) > 60:
            chain.append("...(60+)")
            break
    OUT["chains"][t] = chain

# 2) K2Node_Literal 전수 — ObjectRef 확인
for nid, n in nodes.items():
    if "K2Node_Literal" not in n.get("class", ""):
        continue
    det = call("blueprint_query", "get_node_details", {"asset_path": BP, "graph_name": EG, "node_id": nid})
    props = det.get("properties") or det.get("node", {}).get("properties") or {}
    pins = det.get("pins") or det.get("node", {}).get("pins") or []
    out_pin = next((p for p in pins if p.get("direction") == "output"), {})
    OUT["literals"].append({
        "id": nid, "title": n.get("title"),
        "object_ref": props.get("ObjectRef") or "(props에 없음)",
        "out_pin": out_pin.get("name"),
        "connected": bool(out_pin.get("connected_to")),
    })

# 3) Set WindStrength / WindDirection / Turbulence 노드
for nid, n in nodes.items():
    t = n.get("title") or ""
    if "K2Node_VariableSet" not in n.get("class", ""):
        continue
    if not any(k in t.replace(" ", "") for k in ("WindStrength", "WindDirection", "Turbulence")):
        continue
    pm = pins_map(n)
    rec = {"id": nid, "title": t, "pins": {}}
    for pn, p in pm.items():
        ct = p.get("connected_to") or []
        rec["pins"][pn] = {
            "dir": p.get("direction"), "type": p.get("type"),
            "from_to": [label(c.split(".")[0]) + "." + c.split(".", 1)[1] if "." in c else c for c in ct],
        }
    OUT["windstr_sets"].append(rec)

# 4) Delay 노드와 Duration 소스
for nid, n in nodes.items():
    if "Delay" not in (n.get("title") or ""):
        continue
    pm = pins_map(n)
    dur = pm.get("Duration", {})
    ct = dur.get("connected_to") or []
    OUT["delays"].append({
        "id": nid, "title": n.get("title"),
        "duration_src": [label(c.split(".")[0]) for c in ct] or ["(default: %s)" % dur.get("default_value")],
        "exec_out": [c.split(".")[0][:12] for p in pm.values()
                     if p.get("direction") == "output" and p.get("type") == "exec"
                     for c in (p.get("connected_to") or [])],
    })

print(json.dumps(OUT, ensure_ascii=False, indent=1))
