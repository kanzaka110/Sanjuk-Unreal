# ABP 렛지 대청소 — 2단계: 적용 (2026-07-24)
# ①LedgeState Pred출력 → HandWorld 직결  ②죽은 Set 9개 exec 스플라이스+삭제  ③전용피더 삭제  ④변수 13종 삭제
# 픽폴: 삭제 직전 개별 재조회 / exec 스플라이스는 disconnect→connect 후 링크 검증 / 컴파일 체크
import json, sys, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"

DEAD_SETS = {  # graph -> [(set_node, var)]
    "Ledge_HandTarget": [("K2Node_VariableSet_17", "LedgeHandIdleCompL"), ("K2Node_VariableSet_18", "LedgeHandIdleCompR"),
                         ("K2Node_VariableSet_2", "LedgeHandWorldPredL"), ("K2Node_VariableSet_3", "LedgePrevHandWorldL"),
                         ("K2Node_VariableSet_4", "LedgeHandWorldPredR"), ("K2Node_VariableSet_5", "LedgePrevHandWorldR")],
    "Ledge_FootTarget": [("K2Node_VariableSet_12", "LedgeFootWorldPredL"), ("K2Node_VariableSet_14", "LedgeFootWorldPredR")],
    "Ledge_FootGate": [("K2Node_VariableSet_13", "LedgeFootIKScale")],
}
FEEDERS = json.load(open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/cleanup_plan.json"))
DEL_VARS = ["LedgeHandPrevWL", "LedgeHandPrevWR", "LedgeHandSettle", "LedgePrevWorldNowR",
            "LedgeHandIdleCompL", "LedgeHandIdleCompR", "LedgePrevHandWorldL", "LedgePrevHandWorldR",
            "LedgeHandWorldPredL", "LedgeHandWorldPredR", "LedgeFootWorldPredL", "LedgeFootWorldPredR",
            "LedgeFootIKScale"]


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


def bq(action, params):
    p = {"asset_path": ABP}
    p.update(params)
    return call("blueprint_query", action, p)


def graph(g):
    return {n["id"]: n for n in bq("get_graph_data", {"graph_name": g})["nodes"]}


def pins(nodes, nid):
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


def pie_on():
    r = call("editor_query", "run_python", {
        "command": "import unreal;print(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None)",
        "mode": "execute_file"})
    return "True" in json.dumps(r.get("output", []))


assert not APPLY or not pie_on(), "PIE 실행 중"

# ══ ① LedgeState Pred → HandWorld 직결 ══
ls = graph("LedgeState")
fr = next(nid for nid, n in ls.items() if n["class"] == "K2Node_FunctionResult")
frp = pins(ls, fr)
for pred, world in (("LedgeHandWorldPredL", "LedgeHandWorldL"), ("LedgeHandWorldPredR", "LedgeHandWorldR")):
    srcs = frp[pred]["connected_to"]
    assert len(srcs) == 1, pred + " 소스 다중"
    old_get = srcs[0].split(".")[0]
    assert ls[old_get]["class"] == "K2Node_VariableGet", old_get
    print("[S1]", pred, "<-", old_get, "(교체 예정 ->", world + ")")
    if APPLY:
        r = bq("add_node", {"graph_name": "LedgeState", "node_type": "VariableGet",
                            "variable_name": world, "position": [0, -300 if pred.endswith("L") else -150]})
        newget = r.get("id") or r.get("node_id")
        bq("disconnect_pins", {"graph_name": "LedgeState", "source_node": old_get, "source_pin": pred,
                               "target_node": fr, "target_pin": pred})
        bq("connect_pins", {"graph_name": "LedgeState", "source_node": newget, "source_pin": world,
                            "target_node": fr, "target_pin": pred})
        cur = graph("LedgeState")
        got = pins(cur, fr)[pred]["connected_to"]
        assert got == [newget + "." + world], got
        # 구 Get 삭제 (다른 소비자 없으면)
        outs = [c for p in cur[old_get]["pins"] if p["direction"] == "output" for c in p.get("connected_to", [])]
        if not outs:
            bq("remove_node", {"graph_name": "LedgeState", "node_id": old_get})
            print("[S1] 교체+구Get삭제 완료:", pred)
        else:
            print("[S1] 교체 완료 (구Get 소비자 잔존):", outs)

# ══ ② 죽은 Set exec 스플라이스 + 삭제 ══
for G, sets in DEAD_SETS.items():
    for set_nid, var in sets:
        cur = graph(G)
        if set_nid not in cur:
            print("[S2]", G, set_nid, "이미 없음")
            continue
        pm = pins(cur, set_nid)
        # 변수명 재확인 (ID 드리프트 안전)
        assert var in pm, G + " " + set_nid + " 변수 불일치: " + json.dumps(list(pm.keys()))
        ups = pm.get("execute", {}).get("connected_to", [])
        dns = pm.get("then", {}).get("connected_to", [])
        assert len(dns) <= 1, set_nid + " then 다중"
        print("[S2]", G, set_nid, var, "| exec in:", ups, "-> out:", dns)
        if APPLY:
            for u in ups:
                un, up = u.split(".", 1)
                bq("disconnect_pins", {"graph_name": G, "source_node": un, "source_pin": up,
                                       "target_node": set_nid, "target_pin": "execute"})
                if dns:
                    dn, dp = dns[0].split(".", 1)
                    bq("connect_pins", {"graph_name": G, "source_node": un, "source_pin": up,
                                        "target_node": dn, "target_pin": dp})
            bq("remove_node", {"graph_name": G, "node_id": set_nid})
            print("[S2] 삭제:", set_nid)

# ══ ③ 전용 피더 삭제 (재조회, 소비자 0만) ══
for G, plan in FEEDERS.items():
    for f in plan["feeders"]:
        cur = graph(G)
        if f not in cur:
            print("[S3]", G, f, "이미 없음")
            continue
        outs = [c for p in cur[f]["pins"] if p["direction"] == "output" for c in p.get("connected_to", [])]
        if outs:
            print("[S3] SKIP", G, f, "소비자:", outs)
            continue
        if APPLY:
            bq("remove_node", {"graph_name": G, "node_id": f})
            print("[S3] 삭제:", G, f)
        else:
            print("[S3] 삭제 예정:", G, f, cur[f].get("function") or cur[f]["class"])

# ══ ④ 변수 삭제 ══
if APPLY:
    for v in DEL_VARS:
        try:
            bq("remove_variable", {"name": v})
            print("[S4] -var", v)
        except RuntimeError as e:
            print("[S4] FAIL", v, str(e)[:120])
    r = bq("compile_blueprint", {})
    print("[COMPILE]", json.dumps(r)[:300])
else:
    print("[S4] 삭제 예정 변수:", DEL_VARS)
    print("== dry-run 종료 ==")
