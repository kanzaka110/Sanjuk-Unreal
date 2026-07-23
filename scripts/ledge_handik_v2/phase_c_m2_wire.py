# Phase C M2 — 스플라인 슬라이드 소비 배선 (2026-07-23)
# 검증 근거: probe_c_m1 실측 — destSPL 예측 = 실제 도착 앵커 (소수점 일치, 원통 칸당 요 38°)
# 교체 수학 (4곳: 손L/R, 발L/R):
#   d(α) = Lerp(StartDist, TargetDist, α기존) → fT = GetTransformAtDistanceAlongSpline(SplineRef, d)
#   target = TransformLocation(fT, InverseTransformLocation(StartT, Anchor))
# 손: SelectVector(bPickA=LedgeTransitActive ? 구Lerp : 신규) — 트랜짓은 기존 경로 유지 (Phase T 보존)
# 발: 구Lerp 출력 → Select CF_15/45.B 링크를 신규 출력으로 교체 (트랜짓/정지는 Select bPickA가 이미 A로 분기)
# 구 노드는 연결만 대체, 삭제 없음 (pitfalls 룰)
# 실행: py phase_c_m2_wire.py [apply]
import json, sys, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GH = "Ledge_HandTarget"
GF = "Ledge_FootTarget"
KML = "KismetMathLibrary"
SPL = "SplineComponent"
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


def var_get_nodes(nodes, varname):
    return [nid for nid, n in nodes.items()
            if n["class"] == "K2Node_VariableGet" and any(p["name"] == varname for p in n.get("pins", []))]


def discover(g, anchor_names):
    """umv Subtract → VLerp(슬라이드) 페어 탐지. 반환: {side: {...}}"""
    nodes = graph(g)
    umv_gets = var_get_nodes(nodes, "LedgeUnitMoveVec")
    out = {}
    for nid, n in nodes.items():
        if n["class"] != "K2Node_CallFunction" or n.get("function") != "Subtract_VectorVector":
            continue
        pm = pinsof(nodes, nid)
        a_src = pm.get("A", {}).get("connected_to", [])
        b_src = pm.get("B", {}).get("connected_to", [])
        if not any(c.split(".")[0] in umv_gets for c in b_src):
            continue
        anchor_node = a_src[0].split(".")[0] if a_src else None
        if not anchor_node:
            continue
        anames = [p["name"] for p in nodes[anchor_node].get("pins", []) if p["direction"] == "output"]
        side = None
        for an in anchor_names:
            if an in anames:
                side = an
        if not side:
            continue
        # Subtract 출력 소비자 = 슬라이드 VLerp
        sub_out = pm["ReturnValue"]["connected_to"]
        lerp = None
        for c in sub_out:
            cn, cp = c.rsplit(".", 1)
            if nodes[cn]["class"] == "K2Node_CallFunction" and "Lerp" in str(nodes[cn].get("function")) and cp == "B":
                lerp = cn
        if not lerp:
            continue
        lp = pinsof(nodes, lerp)
        out[side] = {
            "sub": nid, "lerp": lerp,
            "anchor_node": anchor_node, "anchor_pin": side,
            "alpha_src": lp["Alpha"]["connected_to"][0] if lp["Alpha"].get("connected_to") else None,
            "lerp_out_consumers": lp["ReturnValue"]["connected_to"],
        }
    return nodes, out


hn, hand = discover(GH, ["LedgeHandAnchorL", "LedgeHandAnchorR"])
fn, foot = discover(GF, ["LedgeFootAnchorL", "LedgeFootAnchorR"])
print("[PF] hand:", json.dumps(hand, ensure_ascii=False, indent=1))
print("[PF] foot:", json.dumps(foot, ensure_ascii=False, indent=1))
assert len(hand) == 2, "손 슬라이드 페어 2개 미발견"
assert len(foot) == 2, "발 슬라이드 페어 2개 미발견"
for side, d in list(hand.items()) + list(foot.items()):
    assert d["alpha_src"], side + " alpha 소스 없음"
    assert d["lerp_out_consumers"], side + " lerp 소비자 없음"

if not APPLY:
    print("== DRY-RUN OK ==")
    sys.exit(0)

assert not pie_on(), "PIE 실행 중 — 종료 후 apply"

# 백업
for g in (GH, GF):
    exp = bq("export_graph", {"graph_name": g})
    fn2 = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/phaseC_m2_backup_%s.json" % g
    with open(fn2, "w", encoding="utf-8") as f:
        json.dump(exp, f)
    print("[BK]", fn2)


def build_side(g, side, d, base_pos, transit_get):
    """한 사이드의 스플라인 샘플 체인 생성+배선. 반환: 최종 출력 (node, pin)"""
    X, Y = base_pos
    def add(ntype, extra, pos):
        p = {"graph_name": g, "node_type": ntype, "position": pos}
        p.update(extra)
        r = bq("add_node", p)
        return r.get("id") or r.get("node_id")

    def wire(sn, sp, tn, tp):
        bq("connect_pins", {"graph_name": g, "source_node": sn, "source_pin": sp,
                            "target_node": tn, "target_pin": tp})

    vsd = add("VariableGet", {"variable_name": "LedgeMoveStartDist"}, [X, Y + 60])
    vtd = add("VariableGet", {"variable_name": "LedgeMoveTargetDist"}, [X, Y + 120])
    vsp = add("VariableGet", {"variable_name": "LedgeSplineRef"}, [X, Y + 180])
    vst = add("VariableGet", {"variable_name": "LedgeMoveStartT"}, [X, Y + 240])
    dl = add("CallFunction", {"function_class": KML, "function_name": "Lerp"}, [X + 220, Y])
    ft = add("CallFunction", {"function_class": SPL, "function_name": "GetTransformAtDistanceAlongSpline"}, [X + 440, Y])
    inv = add("CallFunction", {"function_class": KML, "function_name": "InverseTransformLocation"}, [X + 440, Y + 220])
    tl = add("CallFunction", {"function_class": KML, "function_name": "TransformLocation"}, [X + 700, Y + 80])
    bq("set_pin_default", {"graph_name": g, "node_id": ft, "pin_name": "CoordinateSpace", "value": "World"})

    wire(vsd, "LedgeMoveStartDist", dl, "A")
    wire(vtd, "LedgeMoveTargetDist", dl, "B")
    asn, asp = d["alpha_src"].rsplit(".", 1)
    wire(asn, asp, dl, "Alpha")
    wire(vsp, "LedgeSplineRef", ft, "self")
    wire(dl, "ReturnValue", ft, "Distance")
    wire(vst, "LedgeMoveStartT", inv, "T")
    wire(d["anchor_node"], d["anchor_pin"], inv, "Location")
    wire(ft, "ReturnValue", tl, "T")
    wire(inv, "ReturnValue", tl, "Location")

    final_n, final_p = tl, "ReturnValue"
    if transit_get:
        sel = add("CallFunction", {"function_class": KML, "function_name": "SelectVector"}, [X + 950, Y + 40])
        wire(d["lerp"], "ReturnValue", sel, "A")
        wire(tl, "ReturnValue", sel, "B")
        wire(transit_get[0], transit_get[1], sel, "bPickA")
        final_n, final_p = sel, "ReturnValue"

    # 구 Lerp 소비자 재배선 (sel.A 제외)
    for c in d["lerp_out_consumers"]:
        cn, cp = c.rsplit(".", 1)
        bq("disconnect_pins", {"graph_name": g, "source_node": d["lerp"], "source_pin": "ReturnValue",
                               "target_node": cn, "target_pin": cp})
        bq("connect_pins", {"graph_name": g, "source_node": final_n, "source_pin": final_p,
                            "target_node": cn, "target_pin": cp})
        print("[REWIRE]", g, side, c, "<-", final_n + "." + final_p)
    return final_n, final_p


# 손: LedgeTransitActive 게터 확보
hn2 = graph(GH)
tget = var_get_nodes(hn2, "LedgeTransitActive")
if tget:
    tnode = tget[0]
else:
    r = bq("add_node", {"graph_name": GH, "node_type": "VariableGet",
                        "variable_name": "LedgeTransitActive", "position": [-5200, 4200]})
    tnode = r.get("id") or r.get("node_id")
    print("[ADD] Get LedgeTransitActive ->", tnode)

finals = {}
finals["HL"] = build_side(GH, "L", hand["LedgeHandAnchorL"], [-5000, 4400], (tnode, "LedgeTransitActive"))
finals["HR"] = build_side(GH, "R", hand["LedgeHandAnchorR"], [-5000, 5000], (tnode, "LedgeTransitActive"))
finals["FL"] = build_side(GF, "L", foot["LedgeFootAnchorL"], [-3000, 2600], None)
finals["FR"] = build_side(GF, "R", foot["LedgeFootAnchorR"], [-3000, 3200], None)

# ══ 검증 ══
ok = True
for g, sides in ((GH, ["LedgeHandAnchorL", "LedgeHandAnchorR"]), (GF, ["LedgeFootAnchorL", "LedgeFootAnchorR"])):
    nodes = graph(g)
    for side in sides:
        d = (hand if g == GH else foot)[side]
        lp = pinsof(nodes, d["lerp"])
        remain = [c for c in lp["ReturnValue"].get("connected_to", [])
                  if "SelectVector" not in nodes.get(c.split(".")[0], {}).get("function", "")
                  and nodes.get(c.split(".")[0], {}).get("function") != "SelectVector"]
        old_left = [c for c in remain if c in d["lerp_out_consumers"]]
        if old_left:
            print("!! 구 소비자 잔존:", g, side, old_left)
            ok = False
if not ok:
    sys.exit(1)
print("[VERIFY] 구 Lerp 소비자 재배선 완료")

r = bq("compile_blueprint", {})
print("[COMPILE]", json.dumps(r, ensure_ascii=False)[:200])
