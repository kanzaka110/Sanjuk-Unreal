# Phase C M3 — yaw-only 프레임 정제 + 미래치 가드 (2026-07-23)
# 실측 근거 (uphill.log):
#   ① 오르막 스플라인 프레임 pitch 31 / roll -11 / roll -180(플립) → 앵커 오프셋 수직 스윙,
#      타깃이 어깨 위 1m (α=1, 도착 프레임에서 dz +104~108)
#   ② 어태치 직후 sd=td=0·StartT=identity 인데 α>0 → gap 610cm 쓰레기 타깃
# 수정:
#   ① GetTransformAtDistanceAlongSpline 5곳(래치 xt + 손L/R + 발L/R) 출력에
#      BreakTransform→BreakRotator→MakeRotator(yaw만)→MakeTransform 새니타이즈 삽입
#   ② eq(sd==td) 를 손 SelectVector bPickA(OR 확장) + 발 Select 게이트 OR 에 합류
# 실행: py phase_c_m3_yawframe.py [apply]
import json, sys, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GH = "Ledge_HandTarget"
GF = "Ledge_FootTarget"
KML = "KismetMathLibrary"
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


def pie_on():
    r = call("editor_query", "run_python", {
        "command": "import unreal;print(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None)",
        "mode": "execute_file"})
    return "True" in json.dumps(r.get("output", []))


def graph(g):
    return {n["id"]: n for n in bq("get_graph_data", {"graph_name": g})["nodes"]}


def pinsof(nodes, nid):
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


# ══ 프리플라이트 ══
plan = {}
for g in (GH, GF):
    nodes = graph(g)
    fts = []
    for nid, n in nodes.items():
        if n["class"] == "K2Node_CallFunction" and n.get("function") == "GetTransformAtDistanceAlongSpline":
            pm = pinsof(nodes, nid)
            cons = pm["ReturnValue"].get("connected_to", [])
            assert len(cons) == 1, nid + " 소비자 1개 아님: " + str(cons)
            fts.append((nid, cons[0], n.get("pos", [0, 0])))
    plan[g] = {"fts": fts}
    print("[PF]", g, "GetTransformAtDistance:", [(f[0], f[1]) for f in fts])
assert len(plan[GH]["fts"]) == 3, "HandTarget에 3개(xt+L+R) 있어야 함"
assert len(plan[GF]["fts"]) == 2, "FootTarget에 2개(L/R) 있어야 함"

# 손 SelectVector (M2 최종 게이트) + bPickA 소스
hn = graph(GH)
sels = [nid for nid, n in hn.items()
        if n["class"] == "K2Node_CallFunction" and n.get("function") == "SelectVector"
        and any(p["name"] == "bPickA" and any("LedgeTransitActive" in str(hn.get(c.split(".")[0], {}).get("pins", [{}])[0].get("name", "")) or
                hn.get(c.split(".")[0], {}).get("class") == "K2Node_VariableGet"
                for c in p.get("connected_to", []))
                for p in n.get("pins", []))]
# 단순화: SelectVector 중 bPickA가 VariableGet(LedgeTransitActive)에 연결된 것
sels = []
for nid, n in hn.items():
    if n["class"] != "K2Node_CallFunction" or n.get("function") != "SelectVector":
        continue
    pm = pinsof(hn, nid)
    src = pm.get("bPickA", {}).get("connected_to", [])
    if src:
        sn = src[0].split(".")[0]
        if hn.get(sn, {}).get("class") == "K2Node_VariableGet" and \
           any(p["name"] == "LedgeTransitActive" for p in hn[sn].get("pins", [])):
            sels.append((nid, sn))
print("[PF] hand SelectVector:", sels)
assert len(sels) == 2, "손 SelectVector 2개 아님"
tget = sels[0][1]

# 발 Select 게이트 (CF_15/45) bPickA 소스 OR
fnodes = graph(GF)
foot_sels = []
for nid in ("K2Node_CallFunction_15", "K2Node_CallFunction_45"):
    pm = pinsof(fnodes, nid)
    src = pm["bPickA"]["connected_to"]
    assert src, nid + " bPickA 소스 없음"
    foot_sels.append((nid, src[0]))
print("[PF] foot gate srcs:", foot_sels)

if not APPLY:
    print("== DRY-RUN OK ==")
    sys.exit(0)

assert not pie_on(), "PIE 실행 중 — 종료 후 apply"

for g in (GH, GF):
    exp = bq("export_graph", {"graph_name": g})
    with open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/phaseC_m3_backup_%s.json" % g, "w", encoding="utf-8") as f:
        json.dump(exp, f)
print("[BK] 백업 완료")


def add(g, ntype, extra, pos):
    p = {"graph_name": g, "node_type": ntype, "position": pos}
    p.update(extra)
    r = bq("add_node", p)
    return r.get("id") or r.get("node_id")


def wire(g, sn, sp, tn, tp):
    bq("connect_pins", {"graph_name": g, "source_node": sn, "source_pin": sp,
                        "target_node": tn, "target_pin": tp})


def disc(g, sn, sp, tn, tp):
    bq("disconnect_pins", {"graph_name": g, "source_node": sn, "source_pin": sp,
                           "target_node": tn, "target_pin": tp})


# ══ ① yaw-only 새니타이즈 삽입 (5곳) ══
for g in (GH, GF):
    for ft, consumer, pos in plan[g]["fts"]:
        cn, cp = consumer.rsplit(".", 1)
        X, Y = pos[0], pos[1] + 380
        bt = add(g, "CallFunction", {"function_class": KML, "function_name": "BreakTransform"}, [X, Y])
        br = add(g, "CallFunction", {"function_class": KML, "function_name": "BreakRotator"}, [X + 200, Y + 60])
        mr = add(g, "CallFunction", {"function_class": KML, "function_name": "MakeRotator"}, [X + 400, Y + 60])
        mt = add(g, "CallFunction", {"function_class": KML, "function_name": "MakeTransform"}, [X + 620, Y])
        bq("set_pin_default", {"graph_name": g, "node_id": mt, "pin_name": "Scale", "value": "1,1,1"})
        disc(g, ft, "ReturnValue", cn, cp)
        wire(g, ft, "ReturnValue", bt, "InTransform")
        wire(g, bt, "Rotation", br, "InRot")
        wire(g, br, "Yaw", mr, "Yaw")
        wire(g, bt, "Location", mt, "Location")
        wire(g, mr, "ReturnValue", mt, "Rotation")
        wire(g, mt, "ReturnValue", cn, cp)
        print("[SANITIZE]", g, ft, "->", consumer)

# ══ ② 미래치 가드 ══
# 공용 eq(sd==td) — 그래프별 생성
for g, targets in ((GH, None), (GF, None)):
    vsd = add(g, "VariableGet", {"variable_name": "LedgeMoveStartDist"}, [-5600, 4200])
    vtd = add(g, "VariableGet", {"variable_name": "LedgeMoveTargetDist"}, [-5600, 4260])
    eq = add(g, "CallFunction", {"function_class": KML, "function_name": "EqualEqual_DoubleDouble"}, [-5400, 4220])
    wire(g, vsd, "LedgeMoveStartDist", eq, "A")
    wire(g, vtd, "LedgeMoveTargetDist", eq, "B")
    if g == GH:
        orn = add(g, "CallFunction", {"function_class": KML, "function_name": "BooleanOR"}, [-5200, 4220])
        wire(g, tget, "LedgeTransitActive", orn, "A")
        wire(g, eq, "ReturnValue", orn, "B")
        for sel, own_src in sels:
            disc(g, own_src, "LedgeTransitActive", sel, "bPickA")
            wire(g, orn, "ReturnValue", sel, "bPickA")
        print("[GUARD] hand OR ->", [s for s, _ in sels])
    else:
        for sel, src in foot_sels:
            sn, sp2 = src.rsplit(".", 1)
            orn = add(g, "CallFunction", {"function_class": KML, "function_name": "BooleanOR"}, [-5200, 4300])
            wire(g, sn, sp2, orn, "A")
            wire(g, eq, "ReturnValue", orn, "B")
            disc(g, sn, sp2, sel, "bPickA")
            wire(g, orn, "ReturnValue", sel, "bPickA")
            print("[GUARD] foot OR ->", sel)

# ══ 검증 + 컴파일 ══
ok = True
for g in (GH, GF):
    nodes = graph(g)
    for ft, consumer, _ in plan[g]["fts"]:
        pm = pinsof(nodes, ft)
        cons = pm["ReturnValue"].get("connected_to", [])
        if any(c == consumer for c in cons):
            print("!! 새니타이즈 미적용:", g, ft)
            ok = False
        if not cons:
            print("!! ft 출력 미연결:", g, ft)
            ok = False
if not ok:
    sys.exit(1)
print("[VERIFY] 새니타이즈 5곳 배선 확인")
r = bq("compile_blueprint", {})
print("[COMPILE]", json.dumps(r, ensure_ascii=False)[:200])
