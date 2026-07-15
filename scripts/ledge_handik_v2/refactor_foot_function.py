# v9.1 — 발 체인을 Ledge_HandTarget에서 분리해 Ledge_FootTarget 함수 신설 (유저 요청)
# A) HandTarget에서 발 노드(빌드 diff) 제거
# B) 공유신호 4개를 멤버변수로 캡처: LedgeRelatch(220)/LedgeStopped(161)/LedgeMoveOffset(167)/LedgePreOffset(199)
#    exec: VS_34 -> 캡처4 -> VS_29 (DestTd 갱신 전 = 신호 살아있는 시점)
# C) Ledge_FootTarget 함수 생성 + 발 체인 재구축 (파라미터 0 — 전부 멤버변수 기반)
# D) 오케스트레이터 Ledge: HandTarget(CF_132) -> FootTarget -> FootGate(CF_133) 스플라이스
import json, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
HT = "Ledge_HandTarget"
FT = "Ledge_FootTarget"
LOG = {"steps": [], "errors": []}


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


# ── A) 발 노드 식별 (프리빌드 덤프와 diff) + 제거 ──
old_ids = {n["id"] for n in json.load(open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/ht_dump.json"))["nodes"]}
g = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": HT})
cur = {n["id"]: n for n in g["nodes"]}
missing_old = [i for i in old_ids if i not in cur]
foot_ids = [i for i in cur if i not in old_ids]
if missing_old:
    raise SystemExit("ID 재할당 감지 — diff 무효, 구조 분류 필요: " + str(missing_old[:8]))
if not (70 <= len(foot_ids) <= 90):
    raise SystemExit("발 노드 수 이상: %d" % len(foot_ids))
LOG["steps"].append("foot nodes: %d, old intact" % len(foot_ids))
for a in ("K2Node_CallFunction_220", "K2Node_CallFunction_161", "K2Node_CallFunction_167",
          "K2Node_CallFunction_199", "K2Node_VariableSet_34", "K2Node_VariableSet_29"):
    if a not in cur:
        raise SystemExit("앵커 소실: " + a)
for nid in foot_ids:
    call("blueprint_query", "remove_node", {"asset_path": ABP, "graph_name": HT, "node_id": nid})
LOG["steps"].append("removed %d foot nodes" % len(foot_ids))

# ── B) 신호 변수 + 캡처 Set 4개 ──
SIGVARS = [("LedgeRelatch", "bool"), ("LedgeStopped", "bool"),
           ("LedgeMoveOffset", "struct:Vector"), ("LedgePreOffset", "struct:Vector")]
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": ABP}).get("variables", [])}
for name, typ in SIGVARS:
    if name not in existing:
        call("blueprint_query", "add_variable",
             {"asset_path": ABP, "name": name, "type": typ, "category": "Ledge|FootIK", "instance_editable": False})
        LOG["steps"].append("var added: " + name)
cap_nodes = [{"temp_id": "cap_" + n, "node_type": "VariableSet", "variable_name": n,
              "position": [4600 + i * 220, 2000]} for i, (n, _) in enumerate(SIGVARS)]
res = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": HT, "nodes": cap_nodes})
tmap = {}
def harvest(obj):
    if isinstance(obj, dict):
        if obj.get("temp_id") and (obj.get("node_id") or obj.get("id")):
            tmap[obj["temp_id"]] = obj.get("node_id") or obj.get("id")
        else:
            for v in obj.values():
                harvest(v)
    elif isinstance(obj, list):
        for e in obj:
            harvest(e)
harvest(res)
if len(tmap) != 4:
    raise SystemExit("캡처 Set 생성 실패: " + json.dumps(res)[:300])
SRC = {"LedgeRelatch": "K2Node_CallFunction_220", "LedgeStopped": "K2Node_CallFunction_161",
       "LedgeMoveOffset": "K2Node_CallFunction_167", "LedgePreOffset": "K2Node_CallFunction_199"}
conns = [{"source_node": SRC[n], "source_pin": "ReturnValue",
          "target_node": tmap["cap_" + n], "target_pin": n} for n, _ in SIGVARS]
call("blueprint_query", "disconnect_pins",
     {"asset_path": ABP, "graph_name": HT, "node_id": "K2Node_VariableSet_34", "pin_name": "then"})
chain = ["K2Node_VariableSet_34"] + [tmap["cap_" + n] for n, _ in SIGVARS] + ["K2Node_VariableSet_29"]
for i in range(len(chain) - 1):
    conns.append({"source_node": chain[i], "source_pin": "then", "target_node": chain[i + 1], "target_pin": "execute"})
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": HT, "connections": conns})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append({"capture_conn_fails": fails})
LOG["steps"].append("capture sets wired (%d fails)" % len(fails))

# ── C) Ledge_FootTarget 함수 생성 + 발 체인 재구축 ──
graphs = [x.get("name", x) if isinstance(x, dict) else x for x in call("blueprint_query", "list_graphs", {"asset_path": ABP}).get("graphs", [])]
if FT not in [str(x) for x in graphs]:
    call("blueprint_query", "add_function", {"asset_path": ABP, "name": FT})
    LOG["steps"].append("function created: " + FT)
gf = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": FT})
entry = None
for n in gf["nodes"]:
    if "FunctionEntry" in n.get("class", ""):
        entry = n["id"]
if not entry:
    raise SystemExit("FunctionEntry 미발견")

KML = "KismetMathLibrary"
CONST = {"L": "7.17,0.61,86.37", "R": "-7.08,4.91,81.19"}
nodes, defaults, conns = [], [], []


def N(tid, ntype, x, y, **kw):
    d = {"temp_id": tid, "node_type": ntype, "position": [x, y]}
    d.update(kw)
    nodes.append(d)


def C(sn, sp, tn, tp):
    conns.append({"source_node": sn, "source_pin": sp, "target_node": tn, "target_pin": tp})


def D(nid, pin, val):
    defaults.append({"node_id": nid, "pin_name": pin, "value": val})


# 공유 소스 (함수 내 신규)
N("g_moveoff", "VariableGet", 100, 200, variable_name="LedgeMoveOffset")
N("g_preoff", "VariableGet", 100, 300, variable_name="LedgePreOffset")
N("g_relatch", "VariableGet", 100, 400, variable_name="LedgeRelatch")
N("g_stopped", "VariableGet", 100, 500, variable_name="LedgeStopped")
N("g_m2w", "VariableGet", 100, 600, variable_name="LedgeMeshToWorld")
N("g_fb", "VariableGet", 100, 700, variable_name="LedgeFrontBlocked")
N("dtn", "CallFunction", 100, 800, function_name="GetWorldDeltaSeconds", target_class="GameplayStatics")
N("compn", "CallFunction", 100, 900, function_name="GetOwningComponent", target_class="AnimInstance")
SH = {"off167": ("g_moveoff", "LedgeMoveOffset"), "off199": ("g_preoff", "LedgePreOffset"),
      "relatch": ("g_relatch", "LedgeRelatch"), "stop": ("g_stopped", "LedgeStopped"),
      "dt": ("dtn", "ReturnValue"), "comp": ("compn", "ReturnValue"),
      "m2w": ("g_m2w", "LedgeMeshToWorld"), "fb": ("g_fb", "LedgeFrontBlocked")}


def CS(key, tn, tp):
    n, p = SH[key]
    C(n, p, tn, tp)


for side in ("L", "R"):
    lo = side.lower()
    yb = 0 if side == "L" else 1000
    p = lambda s: "f%s_%s" % (side, s)
    N(p("wn"), "CallFunction", 400, yb, function_name="TransformLocation", target_class=KML)
    D(p("wn"), "Location", CONST[side])
    CS("m2w", p("wn"), "T")
    N(p("g_anchor"), "VariableGet", 400, yb + 120, variable_name="LedgeFootAnchor" + side)
    N(p("asub"), "CallFunction", 650, yb, function_name="Subtract_VectorVector", target_class=KML)
    C(p("wn"), "ReturnValue", p("asub"), "A")
    CS("off199", p("asub"), "B")
    N(p("asel"), "CallFunction", 900, yb, function_name="SelectVector", target_class=KML)
    C(p("asub"), "ReturnValue", p("asel"), "A")
    C(p("g_anchor"), "LedgeFootAnchor" + side, p("asel"), "B")
    CS("relatch", p("asel"), "bPickA")
    N(p("set_anchor"), "VariableSet", 1150, yb, variable_name="LedgeFootAnchor" + side)
    C(p("asel"), "ReturnValue", p("set_anchor"), "LedgeFootAnchor" + side)
    N(p("dest"), "CallFunction", 650, yb + 220, function_name="Add_VectorVector", target_class=KML)
    C(p("wn"), "ReturnValue", p("dest"), "A")
    CS("off167", p("dest"), "B")
    N(p("mcv"), "CallFunction", 400, yb + 340, function_name="GetCurveValue", target_class="AnimInstance")
    D(p("mcv"), "CurveName", "ledge_foot_move_" + lo)
    N(p("mcc"), "CallFunction", 600, yb + 340, function_name="FClamp", target_class=KML)
    C(p("mcv"), "ReturnValue", p("mcc"), "Value")
    N(p("g_mcb"), "VariableGet", 600, yb + 460, variable_name="LedgeFootMcBase" + side)
    N(p("mcbsel"), "CallFunction", 850, yb + 340, function_name="SelectFloat", target_class=KML)
    C(p("mcc"), "ReturnValue", p("mcbsel"), "A")
    C(p("g_mcb"), "LedgeFootMcBase" + side, p("mcbsel"), "B")
    CS("relatch", p("mcbsel"), "bPickA")
    N(p("set_mcb"), "VariableSet", 1100, yb + 340, variable_name="LedgeFootMcBase" + side)
    C(p("mcbsel"), "ReturnValue", p("set_mcb"), "LedgeFootMcBase" + side)
    N(p("num"), "CallFunction", 850, yb + 460, function_name="Subtract_DoubleDouble", target_class=KML)
    C(p("mcc"), "ReturnValue", p("num"), "A")
    C(p("g_mcb"), "LedgeFootMcBase" + side, p("num"), "B")
    N(p("den"), "CallFunction", 850, yb + 560, function_name="Subtract_DoubleDouble", target_class=KML)
    D(p("den"), "A", "1.0")
    C(p("g_mcb"), "LedgeFootMcBase" + side, p("den"), "B")
    N(p("denmax"), "CallFunction", 1050, yb + 560, function_name="FMax", target_class=KML)
    C(p("den"), "ReturnValue", p("denmax"), "A")
    D(p("denmax"), "B", "0.05")
    N(p("div"), "CallFunction", 1250, yb + 460, function_name="Divide_DoubleDouble", target_class=KML)
    C(p("num"), "ReturnValue", p("div"), "A")
    C(p("denmax"), "ReturnValue", p("div"), "B")
    N(p("mcadj"), "CallFunction", 1450, yb + 460, function_name="FClamp", target_class=KML)
    C(p("div"), "ReturnValue", p("mcadj"), "Value")
    N(p("vlerp"), "CallFunction", 1650, yb + 220, function_name="VLerp", target_class=KML)
    C(p("g_anchor"), "LedgeFootAnchor" + side, p("vlerp"), "A")
    C(p("dest"), "ReturnValue", p("vlerp"), "B")
    C(p("mcadj"), "ReturnValue", p("vlerp"), "Alpha")
    N(p("stopsel"), "CallFunction", 1850, yb + 220, function_name="SelectVector", target_class=KML)
    C(p("wn"), "ReturnValue", p("stopsel"), "A")
    C(p("vlerp"), "ReturnValue", p("stopsel"), "B")
    CS("stop", p("stopsel"), "bPickA")
    N(p("bk1"), "CallFunction", 2050, yb + 220, function_name="BreakVector", target_class=KML)
    C(p("stopsel"), "ReturnValue", p("bk1"), "InVec")
    N(p("bk2"), "CallFunction", 2050, yb + 340, function_name="BreakVector", target_class=KML)
    C(p("wn"), "ReturnValue", p("bk2"), "InVec")
    N(p("mk"), "CallFunction", 2250, yb + 220, function_name="MakeVector", target_class=KML)
    C(p("bk1"), "X", p("mk"), "X")
    C(p("bk1"), "Y", p("mk"), "Y")
    C(p("bk2"), "Z", p("mk"), "Z")
    N(p("sock"), "CallFunction", 2250, yb + 400, function_name="GetSocketLocation", target_class="SceneComponent")
    D(p("sock"), "InSocketName", "thigh_" + lo)
    CS("comp", p("sock"), "self")
    N(p("rel"), "CallFunction", 2450, yb + 220, function_name="Subtract_VectorVector", target_class=KML)
    C(p("mk"), "ReturnValue", p("rel"), "A")
    C(p("sock"), "ReturnValue", p("rel"), "B")
    N(p("len"), "CallFunction", 2650, yb + 300, function_name="VSize", target_class=KML)
    C(p("rel"), "ReturnValue", p("len"), "A")
    N(p("mn"), "CallFunction", 2850, yb + 300, function_name="FMin", target_class=KML)
    C(p("len"), "ReturnValue", p("mn"), "A")
    D(p("mn"), "B", "76.0")
    N(p("nrm"), "CallFunction", 2650, yb + 180, function_name="Normal", target_class=KML)
    C(p("rel"), "ReturnValue", p("nrm"), "A")
    N(p("scaled"), "CallFunction", 3050, yb + 220, function_name="Multiply_VectorFloat", target_class=KML)
    C(p("nrm"), "ReturnValue", p("scaled"), "A")
    C(p("mn"), "ReturnValue", p("scaled"), "B")
    N(p("eff"), "CallFunction", 3250, yb + 220, function_name="Add_VectorVector", target_class=KML)
    C(p("sock"), "ReturnValue", p("eff"), "A")
    C(p("scaled"), "ReturnValue", p("eff"), "B")
    N(p("g_fw"), "VariableGet", 3250, yb + 360, variable_name="LedgeFootWorld" + side)
    N(p("vint"), "CallFunction", 3450, yb + 220, function_name="VInterpTo", target_class=KML)
    C(p("g_fw"), "LedgeFootWorld" + side, p("vint"), "Current")
    C(p("eff"), "ReturnValue", p("vint"), "Target")
    CS("dt", p("vint"), "DeltaTime")
    D(p("vint"), "InterpSpeed", "14.0")
    N(p("set_fw"), "VariableSet", 3650, yb + 220, variable_name="LedgeFootWorld" + side)
    C(p("vint"), "ReturnValue", p("set_fw"), "LedgeFootWorld" + side)
    N(p("inv"), "CallFunction", 3850, yb + 220, function_name="InverseTransformLocation", target_class=KML)
    CS("m2w", p("inv"), "T")
    C(p("g_fw"), "LedgeFootWorld" + side, p("inv"), "Location")
    N(p("set_comp"), "VariableSet", 4050, yb + 220, variable_name="LedgeFootIdleComp" + side)
    C(p("inv"), "ReturnValue", p("set_comp"), "LedgeFootIdleComp" + side)
    N(p("av"), "CallFunction", 3450, yb + 500, function_name="GetCurveValue", target_class="AnimInstance")
    D(p("av"), "CurveName", "ledge_foot_ik_" + lo)
    N(p("avc"), "CallFunction", 3650, yb + 500, function_name="FClamp", target_class=KML)
    C(p("av"), "ReturnValue", p("avc"), "Value")
    N(p("gate"), "CallFunction", 3850, yb + 500, function_name="SelectFloat", target_class=KML)
    C(p("avc"), "ReturnValue", p("gate"), "A")
    D(p("gate"), "B", "0.0")
    CS("fb", p("gate"), "bPickA")
    N(p("g_alpha"), "VariableGet", 3850, yb + 620, variable_name="LedgeFootIKAlpha" + side)
    N(p("fint"), "CallFunction", 4050, yb + 500, function_name="FInterpTo", target_class=KML)
    C(p("g_alpha"), "LedgeFootIKAlpha" + side, p("fint"), "Current")
    C(p("gate"), "ReturnValue", p("fint"), "Target")
    CS("dt", p("fint"), "DeltaTime")
    D(p("fint"), "InterpSpeed", "15.0")
    N(p("set_alpha"), "VariableSet", 4250, yb + 500, variable_name="LedgeFootIKAlpha" + side)
    C(p("fint"), "ReturnValue", p("set_alpha"), "LedgeFootIKAlpha" + side)

res = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": FT, "nodes": nodes})
tmap2 = {}
def harvest2(obj):
    if isinstance(obj, dict):
        if obj.get("temp_id") and (obj.get("node_id") or obj.get("id")):
            tmap2[obj["temp_id"]] = obj.get("node_id") or obj.get("id")
        else:
            for v in obj.values():
                harvest2(v)
    elif isinstance(obj, list):
        for e in obj:
            harvest2(e)
harvest2(res)
if len(tmap2) != len(nodes):
    LOG["errors"].append("FT node mismatch %d/%d" % (len(tmap2), len(nodes)))
for d in defaults:
    d["node_id"] = tmap2.get(d["node_id"], d["node_id"])
rd = call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": ABP, "graph_name": FT, "defaults": defaults})
for c in conns:
    c["source_node"] = tmap2.get(c["source_node"], c["source_node"])
    c["target_node"] = tmap2.get(c["target_node"], c["target_node"])
# exec: Entry -> 앵커L/R -> 맥베이스L/R -> 월드L/R -> 컴포L/R -> 알파L/R
order = ["fL_set_anchor", "fR_set_anchor", "fL_set_mcb", "fR_set_mcb", "fL_set_fw", "fR_set_fw",
         "fL_set_comp", "fR_set_comp", "fL_set_alpha", "fR_set_alpha"]
prev, ppin = entry, "then"
for t in order:
    conns.append({"source_node": prev, "source_pin": ppin, "target_node": tmap2[t], "target_pin": "execute"})
    prev, ppin = tmap2[t], "then"
rc2 = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": FT, "connections": conns})
fails2 = [x for x in (rc2.get("results") or []) if not x.get("success", True)]
if fails2:
    LOG["errors"].append({"ft_conn_fails": fails2})
LOG["steps"].append("FT built: %d nodes, %d links (%d fails)" % (len(tmap2), len(conns), len(fails2)))

# ── D) 오케스트레이터 스플라이스: CF_132(HandTarget) -> FootTarget -> CF_133(FootGate) ──
resD = call("blueprint_query", "add_node",
            {"asset_path": ABP, "graph_name": "Ledge", "node_type": "CallFunction",
             "function_name": FT, "position": [4500, 300]})
ft_call = resD.get("node_id") or resD.get("id")
if not ft_call:
    raise SystemExit("FootTarget 콜노드 생성 실패: " + json.dumps(resD)[:300])
call("blueprint_query", "disconnect_pins",
     {"asset_path": ABP, "graph_name": "Ledge", "node_id": "K2Node_CallFunction_132", "pin_name": "then"})
rcD = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": "Ledge", "connections": [
    {"source_node": "K2Node_CallFunction_132", "source_pin": "then", "target_node": ft_call, "target_pin": "execute"},
    {"source_node": ft_call, "source_pin": "then", "target_node": "K2Node_CallFunction_133", "target_pin": "execute"},
]})
failsD = [x for x in (rcD.get("results") or []) if not x.get("success", True)]
if failsD:
    LOG["errors"].append({"orch_fails": failsD})
LOG["steps"].append("orchestrator spliced (%d fails)" % len(failsD))
LOG["ft_call"] = ft_call

with open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/foot_refactor.json", "w") as fp:
    json.dump(LOG, fp, indent=1, ensure_ascii=False)
print("REFACTOR_DONE errors=%s" % (LOG["errors"] if LOG["errors"] else "none"))
