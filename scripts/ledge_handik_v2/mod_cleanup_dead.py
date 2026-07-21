# AM_SBLedgeIK 죽은 노드 제거 (2026-07-21)
#
# 대상: mod_reachability.py (exec 기준 도달성 + 데이터 역추적) 산출
#   BakePelvisSpring 49 = 구 loop2 속도엔벨로프 잔재 (v9.9 -> 템플릿 베이크 전환 때 exec 절단됨)
#   WriteMoveCurves   1 = RemoveLedgeCurves 중복 호출
#
# ⚠ 2026-07-21 CR 오삭제 사고 교훈:
#   삭제 직전 매번 그래프를 재조회해 "출력이 삭제대상 밖(=살아있는 노드)으로 가는지" 확인하고,
#   하나라도 걸리면 그 노드는 건너뛴다. 스테일 스냅샷 기준으로 지우면 체인이 끊긴다.
import json, urllib.request

URL = "http://localhost:9316/mcp"
BP = "/Game/Art/TA/AnimModifiers/AM_SBLedgeIK"
REACH = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/mod_reach.json"
OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/mod_cleanup.json"
log = {"removed": {}, "skipped": {}, "errors": []}


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


reach = json.load(open(REACH))
for gname, r in reach["graphs"].items():
    targets = list(r["dead"])
    if not targets:
        continue
    tset = set(targets)
    log["removed"][gname] = []
    log["skipped"][gname] = []
    for name in targets:
        g = call("blueprint_query", "get_graph_data", {"asset_path": BP, "graph_name": gname})  # ★ 매번 재조회
        nodes = {n["id"]: n for n in g["nodes"]}
        if name not in nodes:
            log["skipped"][gname].append({name: "이미 없음"})
            continue
        ext = []
        for p in nodes[name]["pins"]:
            if p["direction"] != "output":
                continue
            for c in p.get("connected_to") or []:
                tgt = c.split(".")[0]
                if tgt not in tset:
                    ext.append(tgt)
        if ext:
            log["skipped"][gname].append({name: "살아있는 소비자: %s" % sorted(set(ext))})
            continue
        try:
            call("blueprint_query", "remove_node", {"asset_path": BP, "graph_name": gname, "node_id": name})
            log["removed"][gname].append(name)
        except Exception as e:
            log["errors"].append({gname + "/" + name: str(e)[:140]})

json.dump(log, open(OUT, "w"), indent=1, ensure_ascii=False)
tot_r = sum(len(v) for v in log["removed"].values())
tot_s = sum(len(v) for v in log["skipped"].values())
print("MOD_CLEANUP_DONE removed=%d skipped=%d err=%d" % (tot_r, tot_s, len(log["errors"])))
for g, v in log["removed"].items():
    print("  [%s] 제거 %d" % (g, len(v)))
for g, v in log["skipped"].items():
    for s in v[:5]:
        print("  [%s] SKIP %s" % (g, s))
