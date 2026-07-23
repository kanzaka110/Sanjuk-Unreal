# Phase C 후 정리 — Ledge_HandTarget / Ledge_FootTarget 미사용 노드·변수 삭제 (2026-07-23)
# 도달성 정의:
#   live-exec = FunctionEntry에서 exec 링크로 도달 가능한 노드
#   live-data = live-exec 노드들의 입력 핀에 (퓨어 체인 경유 포함) 기여하는 모든 노드
#   dead = 그 외 전부 (코멘트 제외)
# 변수: 노드 삭제 후 그래프 전체(find_variable_references) 참조 0인 PhaseC 계열만 삭제
# 실행: py phase_c_cleanup.py [apply]
import json, sys, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GRAPHS = ["Ledge_HandTarget", "Ledge_FootTarget"]
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"
VAR_CANDIDATES = ["LedgeIdleSnapL", "LedgeIdleSnapR", "LedgeSnapValid"]


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:400])
    return json.loads(txt)


def bq(action, params):
    p = {"asset_path": ABP}
    p.update(params)
    return call("blueprint_query", action, p)


def pie_on():
    r = call("editor_query", "run_python", {
        "command": "import unreal;print(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None)",
        "mode": "execute_file"})
    return "True" in json.dumps(r.get("output", []))


def analyze(g):
    d = bq("get_graph_data", {"graph_name": g})
    nodes = {n["id"]: n for n in d["nodes"]}
    entry = [nid for nid, n in nodes.items() if n["class"] == "K2Node_FunctionEntry"]
    assert entry, g + " entry 없음"

    # exec 전방 BFS
    live = set(entry)
    frontier = list(entry)
    while frontier:
        nid = frontier.pop()
        for p in nodes[nid].get("pins", []):
            if p.get("type") == "exec" and p["direction"] == "output":
                for c in p.get("connected_to", []):
                    cn = c.split(".")[0]
                    if cn in nodes and cn not in live:
                        live.add(cn)
                        frontier.append(cn)
    live_exec = set(live)

    # 데이터 역방향: live 노드 입력에 기여하는 소스 전부
    frontier = list(live)
    while frontier:
        nid = frontier.pop()
        for p in nodes[nid].get("pins", []):
            if p["direction"] == "input":
                for c in p.get("connected_to", []):
                    cn = c.split(".")[0]
                    if cn in nodes and cn not in live:
                        live.add(cn)
                        frontier.append(cn)

    dead = [nid for nid in nodes
            if nid not in live and nodes[nid]["class"] != "EdGraphNode_Comment"]
    return nodes, live_exec, live, dead


plan = {}
for g in GRAPHS:
    nodes, le, lv, dead = analyze(g)
    plan[g] = (nodes, dead)
    print("=== %s: 전체 %d / live %d / dead %d ===" % (g, len(nodes), len(lv), len(dead)))
    for nid in sorted(dead):
        n = nodes[nid]
        label = n.get("function") or n.get("macro_name") or n["class"]
        vpin = next((p["name"] for p in n.get("pins", []) if p["name"].startswith("Ledge")), "")
        print("  DEAD", nid, label, vpin)

if not APPLY:
    print("== DRY-RUN — 리스트 검토 후 apply ==")
    sys.exit(0)

assert not pie_on(), "PIE 실행 중 — 종료 후 apply"

# 백업
for g in GRAPHS:
    exp = bq("export_graph", {"graph_name": g})
    fn = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/phaseC_cleanup_backup_%s.json" % g
    with open(fn, "w", encoding="utf-8") as f:
        json.dump(exp, f)
    print("[BK]", fn)

# 삭제
for g in GRAPHS:
    nodes, dead = plan[g]
    for nid in dead:
        try:
            bq("remove_node", {"graph_name": g, "node_id": nid})
            print("[DEL]", g, nid)
        except Exception as ex:
            print("[DEL FAIL]", g, nid, str(ex)[:120])

# 컴파일 1차
r = bq("compile_blueprint", {})
print("[COMPILE]", json.dumps(r, ensure_ascii=False)[:300])
assert r.get("error_count", 1) == 0, "컴파일 에러 — 중단"

# 변수 정리 (참조 0 확인 후)
for v in VAR_CANDIDATES:
    try:
        refs = bq("find_variable_references", {"variable_name": v})
        cnt = refs.get("reference_count", refs.get("count", None))
        if cnt is None:
            cnt = len(refs.get("references", []))
        if cnt == 0:
            bq("remove_variable", {"variable_name": v})
            print("[VAR DEL]", v)
        else:
            print("[VAR KEEP]", v, "refs:", cnt)
    except Exception as ex:
        print("[VAR FAIL]", v, str(ex)[:150])

r = bq("compile_blueprint", {})
print("[COMPILE2]", json.dumps(r, ensure_ascii=False)[:300])
