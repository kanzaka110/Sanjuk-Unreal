# AM_SBLedgeIK 도달성 분석 (로컬, read-only) — 죽은 노드 / 미사용 변수 후보
#
# ⚠ 2026-07-21 CR 사고 교훈 반영:
#   - knot(경유 노드)의 링크를 반드시 양방향 추적할 것. IO 핀을 입력에서 빼면 knot 뒤 체인을
#     통째로 놓쳐 살아있는 클러스터를 '죽음'으로 오판한다 (CR 왼손 이펙터 오삭제의 직접 원인)
#   - 분석 결과는 보고만. 삭제는 사용자 승인 후 별도 스크립트로.
import json, urllib.request

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/TA/AnimModifiers/AM_SBLedgeIK"
OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/mod_reach.json"


def call(tool, action, params, timeout=300):
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:300])
    return json.loads(txt)


graphs = [g["name"] for g in call("blueprint_query", "list_graphs", {"asset_path": BP})["graphs"]]
report = {"graphs": {}, "dump": {}}
var_used = {}

for gname in graphs:
    g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": gname})
    report["dump"][gname] = g
    nodes = {n["id"]: n for n in g["nodes"]}

    # 시작점: 이벤트 / 함수 엔트리
    roots = [nid for nid, n in nodes.items()
             if "Event" in n.get("class", "") or "FunctionEntry" in n.get("class", "")]

    # 인접 관계: 노드 -> 노드 (방향 무시하고 '연결되어 있음'으로 exec 체인 추적)
    # ⚠ exec 과 데이터를 구분해야 한다. 데이터 출력으로도 전파하면 exec 이 끊긴 죽은 클러스터가
    #   '살아있음'으로 잡혀 과소 탐지된다 (BakePelvisSpring 의 구 loop2 dead 를 놓친 원인).
    def out_targets(nid):
        t = set()
        for p in nodes[nid]["pins"]:
            if p["direction"] != "output" or p.get("type") != "exec":
                continue
            for c in p.get("connected_to") or []:
                t.add(c.split(".")[0])
        return t

    def in_sources(nid):
        s = set()
        for p in nodes[nid]["pins"]:
            if p["direction"] not in ("input",):
                continue
            for c in p.get("connected_to") or []:
                s.add(c.split(".")[0])
        return s

    # 1) 루트에서 출력 방향으로 도달 (exec 흐름)
    alive, frontier = set(roots), list(roots)
    while frontier:
        nid = frontier.pop()
        for t in out_targets(nid):
            if t in nodes and t not in alive:
                alive.add(t)
                frontier.append(t)
    # 2) 살아있는 노드의 '입력'을 역추적 (데이터 공급자)
    frontier = list(alive)
    while frontier:
        nid = frontier.pop()
        for s in in_sources(nid):
            if s in nodes and s not in alive:
                alive.add(s)
                frontier.append(s)

    dead = sorted(set(nodes) - alive)
    report["graphs"][gname] = {"total": len(nodes), "alive": len(alive), "dead": dead,
                               "dead_titles": {d: str(nodes[d].get("title"))[:40] for d in dead}}

    # 변수 사용 수집
    for nid, n in nodes.items():
        cls = n.get("class", "")
        if "VariableGet" in cls or "VariableSet" in cls:
            title = str(n.get("title", ""))
            vn = title.replace("Get ", "").replace("Set ", "").strip()
            var_used.setdefault(vn, []).append((gname, nid, nid in alive))
        # 함수 호출 인자로 변수가 쓰이는 경우는 위 Get 노드로 잡힘

report["var_used"] = {k: {"nodes": len(v), "alive": sum(1 for x in v if x[2])} for k, v in var_used.items()}
json.dump(report, open(OUT, "w"), indent=1, ensure_ascii=False)

print("=== 그래프별 도달성")
for gname, r in report["graphs"].items():
    print("  %-20s 노드 %3d / 살아있음 %3d / 죽음 %2d" % (gname, r["total"], r["alive"], len(r["dead"])))
print()
for gname, r in report["graphs"].items():
    if not r["dead"]:
        continue
    print("[%s] 죽은 노드 %d:" % (gname, len(r["dead"])))
    for d in r["dead"]:
        print("    %-28s %s" % (d, r["dead_titles"][d]))
print()
print("=== 변수 노드 사용 현황 (그래프 내 Get/Set 노드 기준)")
for k, v in sorted(report["var_used"].items()):
    mark = "✅" if v["alive"] else "⚠ 전부 죽음"
    print("  %-28s 노드 %d / 살아있음 %d  %s" % (k, v["nodes"], v["alive"], mark))
