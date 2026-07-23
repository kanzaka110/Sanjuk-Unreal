# Phase C — M4 검증상태 전체 복원 (2026-07-23)
# phaseC_m5_backup_Ledge_HandTarget.json (= M4 최종, 유저 검증) 기준으로
# 현재 그래프와의 연결 diff를 전부 원복: extra 링크 disconnect → missing 링크 connect → 컴파일
# 실행: py phase_c_restore_m4.py apply
import json, sys, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
G = "Ledge_HandTarget"
BAK = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/phaseC_m5_backup_Ledge_HandTarget.json"
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"


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


cur = bq("get_graph_data", {"graph_name": G})
curE = set()
for n in cur["nodes"]:
    for p in n.get("pins", []):
        if p["direction"] == "output":
            for c in p.get("connected_to", []):
                curE.add((n["id"] + "." + p["name"], c))
bak = json.load(open(BAK))
bakE = set((c["from_node"] + "." + c["from_pin"], c["to_node"] + "." + c["to_pin"])
           for c in bak["connections"])
missing = sorted(bakE - curE)
extra = sorted(curE - bakE)
print("missing:", len(missing), "extra:", len(extra))
for m in missing:
    print("  -", m)
for e in extra:
    print("  +", e)

if not APPLY:
    print("== DRY-RUN ==")
    sys.exit(0)


def split(edge):
    s, t = edge
    sn, sp = s.rsplit(".", 1)
    tn, tp = t.rsplit(".", 1)
    return sn, sp, tn, tp


ok, fail = 0, 0
for e in extra:
    sn, sp, tn, tp = split(e)
    try:
        bq("disconnect_pins", {"graph_name": G, "source_node": sn, "source_pin": sp,
                               "target_node": tn, "target_pin": tp})
        ok += 1
    except Exception as ex:
        print("[DISC FAIL]", e, str(ex)[:120])
        fail += 1
for m in missing:
    sn, sp, tn, tp = split(m)
    try:
        bq("connect_pins", {"graph_name": G, "source_node": sn, "source_pin": sp,
                            "target_node": tn, "target_pin": tp})
        ok += 1
    except Exception as ex:
        print("[CONN FAIL]", m, str(ex)[:120])
        fail += 1
print("ops ok=%d fail=%d" % (ok, fail))

# 재검증
cur2 = bq("get_graph_data", {"graph_name": G})
curE2 = set()
for n in cur2["nodes"]:
    for p in n.get("pins", []):
        if p["direction"] == "output":
            for c in p.get("connected_to", []):
                curE2.add((n["id"] + "." + p["name"], c))
print("잔여 missing:", len(bakE - curE2), "잔여 extra:", len(curE2 - bakE))
for x in sorted(bakE - curE2):
    print("  still missing:", x)
for x in sorted(curE2 - bakE):
    print("  still extra:", x)
r = bq("compile_blueprint", {})
print("[COMPILE]", json.dumps(r, ensure_ascii=False)[:200])
