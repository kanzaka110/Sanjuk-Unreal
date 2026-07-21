# CR 도달성 분석 (로컬, read-only) — 죽은 노드 / 미사용 변수 후보 산출
# exec 체인에서 시작해 데이터 입력을 역추적한 폐포 = 살아있는 노드.
# ⚠ 삭제는 하지 않는다. CR 은 잘못 지우면 크래시 이력 있음 (current-unreal.md) → 목록만 보고.
import json, sys

SRC = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/cr_snapshot_pre_ankle.json"
d = json.load(open(SRC))
nodes = d["nodes"]


def pins(nid):
    return nodes.get(nid, {}).get("pins", [])


def is_exec(p):
    return "ExecuteContext" in p.get("type", "")


# 1) exec 체인 수집 (exec 링크로 연결된 노드 전부)
exec_nodes = set()
for nid, v in nodes.items():
    for p in v["pins"]:
        if is_exec(p) and p["links"]:
            exec_nodes.add(nid)
            for l in p["links"]:
                exec_nodes.add(l.split(".")[0])

# 2) 데이터 폐포: exec 노드의 입력을 역추적
alive = set(exec_nodes)
frontier = list(exec_nodes)
while frontier:
    nid = frontier.pop()
    for p in pins(nid):
        if is_exec(p):
            continue
        # ⚠ Reroute(knot)의 핀은 방향이 IO 다. IO 를 입력에서 빼면 knot 뒤 체인을 통째로 못 따라가
        #   살아있는 클러스터를 '죽음'으로 오판한다 (2026-07-21 왼손 이펙터 오삭제 사고의 직접 원인).
        if "INPUT" not in p["dir"] and "IO" not in p["dir"]:
            continue
        for l in p["links"]:
            src = l.split(".")[0]
            if src not in alive:
                alive.add(src)
                frontier.append(src)

dead = sorted(set(nodes) - alive)

# 3) 변수 사용 현황
varnodes = {}
for nid, v in nodes.items():
    for p in v["pins"]:
        if p["pin"] == "Variable":
            varnodes.setdefault(p["default"], []).append((nid, nid in alive))

print("총 %d 노드 / 살아있음 %d / 죽음 %d" % (len(nodes), len(alive), len(dead)))
print()
print("=== 죽은 노드 후보 (%d)" % len(dead))
for nid in dead:
    v = nodes[nid]
    print("   %-26s %-38s pos=%s" % (nid, v["struct"][:38] or "(variable)", v.get("pos")))
print()
print("=== 변수 사용 현황")
declared = {v["name"] for v in d.get("variables", [])}
for name in sorted(declared):
    used = varnodes.get(name, [])
    live = [n for n, a in used if a]
    if not used:
        print("   %-20s ❌ 노드 없음 (완전 미사용)" % name)
    elif not live:
        print("   %-20s ⚠ 노드 %d개 전부 죽음: %s" % (name, len(used), [n for n, _ in used]))
    else:
        print("   %-20s ✅ 사용중 (%d노드)" % (name, len(live)))
orphan = set(varnodes) - declared
if orphan:
    print("   미선언 변수 참조:", orphan)
