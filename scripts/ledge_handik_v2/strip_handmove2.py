# HandMove2 (손 2차 창) 로직 + 변수 제거 (2026-07-21, 유저 지시)
#
# 배경: HandMove2 값은 전 애님 0 (derive_windows2 일괄 산출 잔재였고 유저 수작업분 아님).
#       Branch 조건이 (End > Start) 라 값 0이면 이미 실행되지 않지만, 파라미터 목록에서 없애기 위해 로직까지 제거.
#       ⚠ FootMove2 는 유저 수작업 4종이 사용 중이므로 절대 건드리지 않는다.
#
# exec:  Knot_35 -> Branch_4(손2차L) -> Branch_5(손2차R) -> Branch_6(발2차, 유지)
#   => Knot_35 를 Branch_6 에 직결하고 Branch_4/5 와 그 then 체인을 제거.
#
# 백업: am_ledgeik_FULL_BACKUP.json (6그래프 전체)
import json, urllib.request

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/TA/AnimModifiers/AM_SBLedgeIK"
G = "WriteMoveCurves"
OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/strip_handmove2.json"
B4, B5, B6 = "K2Node_IfThenElse_4", "K2Node_IfThenElse_5", "K2Node_IfThenElse_6"
SRC_KNOT = "K2Node_Knot_35"
VARS = ["HandMove2StartL", "HandMove2EndL", "HandMove2StartR", "HandMove2EndR"]
log = {"steps": [], "candidates": [], "removed": [], "skipped": [], "errors": []}


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:250])
    return json.loads(txt)


g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": G})
nodes = {n["id"]: n for n in g["nodes"]}
for anchor in (B4, B5, B6, SRC_KNOT):
    if anchor not in nodes:
        raise SystemExit("앵커 없음: " + anchor)

STOP = {B6}


def exec_outs(nid):
    out = []
    for p in nodes[nid]["pins"]:
        if p["direction"] == "output" and p.get("type") == "exec":
            for c in p.get("connected_to") or []:
                out.append(c.split(".")[0])
    return out


# 1) exec 후보: Branch_4/5 와 그 then 체인 (Branch_6 이전까지)
cand, stack = set(), [B4, B5]
while stack:
    nid = stack.pop()
    if nid in STOP or nid in cand or nid not in nodes:
        continue
    cand.add(nid)
    for t in exec_outs(nid):
        stack.append(t)

# 2) 데이터 공급자 흡수: 후보에만 데이터를 주는 노드 (후보 밖 소비자가 있으면 제외)
def consumers(nid):
    out = set()
    for p in nodes[nid]["pins"]:
        if p["direction"] != "output":
            continue
        for c in p.get("connected_to") or []:
            out.add(c.split(".")[0])
    return out


changed = True
while changed:
    changed = False
    for nid, n in nodes.items():
        if nid in cand or nid in STOP:
            continue
        cons = consumers(nid)
        if not cons:
            continue
        if cons and cons <= cand:          # 소비자가 전부 삭제 후보 안에만 있음
            cand.add(nid)
            changed = True

log["candidates"] = sorted(cand)
log["steps"].append("삭제 후보 %d개" % len(cand))

# 3) exec 재연결: Knot_35 -> Branch_6
call("blueprint_query", "disconnect_pins", {"asset_path": BP, "graph_name": G,
                                            "node_id": SRC_KNOT, "pin_name": "OutputPin"})
call("blueprint_query", "disconnect_pins", {"asset_path": BP, "graph_name": G,
                                            "node_id": B6, "pin_name": "execute"})
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": BP, "graph_name": G, "connections": [
    {"source_node": SRC_KNOT, "source_pin": "OutputPin", "target_node": B6, "target_pin": "execute"}]})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    raise SystemExit("exec 재연결 실패 — 중단: " + json.dumps(fails)[:200])
log["steps"].append("exec 재연결 Knot_35 -> Branch_6")

# 4) 노드 제거 (매번 재조회 + 외부 소비자 재확인)
for name in sorted(cand):
    cur = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": G})
    cn = {n["id"]: n for n in cur["nodes"]}
    if name not in cn:
        log["skipped"].append({name: "이미 없음"})
        continue
    ext = []
    for p in cn[name]["pins"]:
        if p["direction"] != "output":
            continue
        for c in p.get("connected_to") or []:
            t = c.split(".")[0]
            if t not in cand:
                ext.append(t)
    if ext:
        log["skipped"].append({name: "외부 소비자 %s" % sorted(set(ext))})
        continue
    try:
        call("blueprint_query", "remove_node", {"asset_path": BP, "graph_name": G, "node_id": name})
        log["removed"].append(name)
    except Exception as e:
        log["errors"].append({name: str(e)[:120]})

# 5) 변수 제거
for v in VARS:
    try:
        call("blueprint_query", "remove_variable", {"asset_path": BP, "name": v})
        log["steps"].append("변수 제거: " + v)
    except Exception as e:
        log["errors"].append({v: str(e)[:120]})

json.dump(log, open(OUT, "w"), indent=1, ensure_ascii=False)
print("STRIP_HANDMOVE2 removed=%d skipped=%d err=%d" % (len(log["removed"]), len(log["skipped"]), len(log["errors"])))
for s in log["steps"]:
    print("  " + s)
for s in log["skipped"][:8]:
    print("  SKIP", s)
for e in log["errors"][:5]:
    print("  ERR", e)
