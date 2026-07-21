# 손 타깃 1프레임 외삽 (2026-07-21) — 발(foot_target_lead.py)과 동일 처방을 손에 이식
#
# 근거: 손 타깃(LedgeHandWorldL/R)도 UpdateVariables(평가 전=전프레임 포즈)에서 계산 → 1~2프레임 지연.
#       발 실측(probe_ankle): 오차 = 1.0 x 타깃이동량 → 외삽으로 상쇄 확인.
# ⚠ 손 특유 위험: 릴리즈 중 타깃=손 소켓 추적(자가오염 함정) → K 0.8 / 상한 10cm 보수 설정,
#       릴리즈 중엔 알파 하강(25)이라 IK 영향 자체가 작음.
#
# 배선: [Ledge_HandTarget] SetWorldR(VS_21) -> SetPredL/R -> SetPrevL/R -> VS_17(기존)
#       pred = world + Clamp((world - prev) x K, 10)
#       [AnimGraph] CR 핀 HandTargetL/R <- LedgeHandWorldPredL/R 로 교체
# 백업: handtarget_dump.json (192노드) / abp_animgraph_dump.json
import json, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
HT = "Ledge_HandTarget"
KML = "KismetMathLibrary"
K = 0.8
MAXLEAD = 10.0
LOG = {"steps": [], "fails": []}


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


# ── 사전 검증 ──
g = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": HT})
nodes = {n["id"]: n for n in g["nodes"]}


def pin_src(nid, pname):
    for p in nodes[nid]["pins"]:
        if p["name"] == pname:
            return (p.get("connected_to") or [None])[0]
    return None


if pin_src("K2Node_VariableSet_21", "execute") != "K2Node_VariableSet_20.then":
    raise SystemExit("앵커 불일치: VS_20 -> VS_21 체인")
after = pin_src("K2Node_VariableSet_17", "execute")
if after != "K2Node_VariableSet_21.then":
    raise SystemExit("앵커 불일치: VS_21 -> VS_17 (실제: %s)" % after)
LOG["steps"].append("anchors verified")

# ── 변수 4개 ──
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": ABP}).get("variables", [])}
for nm in ("LedgePrevHandWorldL", "LedgePrevHandWorldR", "LedgeHandWorldPredL", "LedgeHandWorldPredR"):
    if nm not in existing:
        call("blueprint_query", "add_variable",
             {"asset_path": ABP, "name": nm, "type": "struct:Vector", "category": "Ledge|HandIK", "instance_editable": False})
        LOG["steps"].append("var: " + nm)

# ── 노드 생성 ──
specs, conns, defaults = [], [], []


def N(tid, ntype, x, y, **kw):
    d = {"temp_id": tid, "node_type": ntype, "position": [x, y]}
    d.update(kw)
    specs.append(d)


def C(sn, sp, tn, tp):
    conns.append({"source_node": sn, "source_pin": sp, "target_node": tn, "target_pin": tp})


for s in ("L", "R"):
    yb = 3000 if s == "L" else 3400
    p = lambda k: "hlead%s_%s" % (s, k)
    N(p("gw"), "VariableGet", 5200, yb, variable_name="LedgeHandWorld" + s)
    N(p("gp"), "VariableGet", 5200, yb + 100, variable_name="LedgePrevHandWorld" + s)
    N(p("sub"), "CallFunction", 5450, yb, function_name="Subtract_VectorVector", target_class=KML)
    N(p("mul"), "CallFunction", 5650, yb, function_name="Multiply_VectorFloat", target_class=KML)
    N(p("clm"), "CallFunction", 5850, yb, function_name="ClampVectorSize", target_class=KML)
    N(p("add"), "CallFunction", 6050, yb, function_name="Add_VectorVector", target_class=KML)
    N(p("spred"), "VariableSet", 6250, yb, variable_name="LedgeHandWorldPred" + s)
    N(p("sprev"), "VariableSet", 6250, yb + 160, variable_name="LedgePrevHandWorld" + s)

res = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": HT, "nodes": specs})
tmap = {}


def harvest(o):
    if isinstance(o, dict):
        if o.get("temp_id") and (o.get("node_id") or o.get("id")):
            tmap[o["temp_id"]] = o.get("node_id") or o.get("id")
        else:
            for v in o.values():
                harvest(v)
    elif isinstance(o, list):
        for e in o:
            harvest(e)


harvest(res)
if len(tmap) != len(specs):
    raise SystemExit("노드 생성 불일치 %d/%d" % (len(tmap), len(specs)))
LOG["steps"].append("nodes created: %d" % len(tmap))

for s in ("L", "R"):
    t = lambda k: tmap["hlead%s_%s" % (s, k)]
    defaults.append({"node_id": t("mul"), "pin_name": "B", "value": str(K)})
    defaults.append({"node_id": t("clm"), "pin_name": "Max", "value": str(MAXLEAD)})
    C(t("gw"), "LedgeHandWorld" + s, t("sub"), "A")
    C(t("gp"), "LedgePrevHandWorld" + s, t("sub"), "B")
    C(t("sub"), "ReturnValue", t("mul"), "A")
    C(t("mul"), "ReturnValue", t("clm"), "A")
    C(t("gw"), "LedgeHandWorld" + s, t("add"), "A")
    C(t("clm"), "ReturnValue", t("add"), "B")
    C(t("add"), "ReturnValue", t("spred"), "LedgeHandWorldPred" + s)
    C(t("gw"), "LedgeHandWorld" + s, t("sprev"), "LedgePrevHandWorld" + s)

call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": ABP, "graph_name": HT, "defaults": defaults})

# exec 스플라이스: VS_21 -> PredL -> PredR -> PrevL -> PrevR -> VS_17
call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": HT,
                                            "node_id": "K2Node_VariableSet_21", "pin_name": "then"})
chain = ["K2Node_VariableSet_21", tmap["hleadL_spred"], tmap["hleadR_spred"],
         tmap["hleadL_sprev"], tmap["hleadR_sprev"], "K2Node_VariableSet_17"]
for a, b in zip(chain, chain[1:]):
    C(a, "then", b, "execute")

rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": HT, "connections": conns})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
LOG["fails"] += fails
LOG["steps"].append("HT links %d (%d fails)" % (len(conns), len(fails)))

# ── AnimGraph: CR 핀 소스를 Pred 로 교체 ──
ag_specs = [
    {"temp_id": "ag_gpl", "node_type": "VariableGet", "variable_name": "LedgeHandWorldPredL", "position": [-400, 1200]},
    {"temp_id": "ag_gpr", "node_type": "VariableGet", "variable_name": "LedgeHandWorldPredR", "position": [-400, 1300]},
]
res2 = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": "AnimGraph", "nodes": ag_specs})
tmap2 = {}


def harvest2(o):
    if isinstance(o, dict):
        if o.get("temp_id") and (o.get("node_id") or o.get("id")):
            tmap2[o["temp_id"]] = o.get("node_id") or o.get("id")
        else:
            for v in o.values():
                harvest2(v)
    elif isinstance(o, list):
        for e in o:
            harvest2(e)


harvest2(res2)
if len(tmap2) != 2:
    raise SystemExit("AnimGraph Get 생성 실패")
for pin_name in ("HandTargetL", "HandTargetR"):
    call("blueprint_query", "disconnect_pins", {"asset_path": ABP, "graph_name": "AnimGraph",
                                                "node_id": "AnimGraphNode_ControlRig_1", "pin_name": pin_name})
rc2 = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": "AnimGraph", "connections": [
    {"source_node": tmap2["ag_gpl"], "source_pin": "LedgeHandWorldPredL", "target_node": "AnimGraphNode_ControlRig_1", "target_pin": "HandTargetL"},
    {"source_node": tmap2["ag_gpr"], "source_pin": "LedgeHandWorldPredR", "target_node": "AnimGraphNode_ControlRig_1", "target_pin": "HandTargetR"},
]})
fails2 = [x for x in (rc2.get("results") or []) if not x.get("success", True)]
LOG["fails"] += fails2
LOG["steps"].append("AnimGraph rewire (%d fails)" % len(fails2))

json.dump(LOG, open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/hand_lead.json", "w"), indent=1, ensure_ascii=False)
print("HAND_LEAD_DONE fails=%d" % len(LOG["fails"]))
for s in LOG["steps"]:
    print("  " + s)
