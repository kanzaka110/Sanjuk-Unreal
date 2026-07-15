# Ledge_HandTarget 발 체인 확장 (FrontBlocked 벽짚기 Foot IK, 핸드 구조 미러) — v9 Stage 3
# 공유 재사용: 횡축오프셋 CF_167/199, 재래치 CF_220, 정지판정 CF_161, dt CF_123, 컴포넌트 CF_113,
#             M2W VG_72/42, FrontBlocked VG_71
# 신규: 변수 10개 + 노드 ~78 (L/R 미러) + exec 스플라이스 2곳
# ⚠ 실행 전제: 직전 컴파일 이후 그래프 무변경 (노드 ID 유효)
import json, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
G = "Ledge_HandTarget"
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


# ── 0) 프리플라이트: 앵커 노드 존재 확인 ──
ANCHORS = ["K2Node_CallFunction_167", "K2Node_CallFunction_199", "K2Node_CallFunction_220",
           "K2Node_CallFunction_161", "K2Node_CallFunction_123", "K2Node_CallFunction_113",
           "K2Node_VariableGet_72", "K2Node_VariableGet_42", "K2Node_VariableGet_71",
           "K2Node_VariableSet_34", "K2Node_VariableSet_29", "K2Node_VariableSet_1"]
g = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": G})
ids = {n["id"] for n in g["nodes"]}
missing = [a for a in ANCHORS if a not in ids]
if missing:
    raise SystemExit("ANCHOR MISSING (스테일 ID — 재덤프 필요): " + str(missing))
LOG["steps"].append("preflight OK (%d nodes)" % len(ids))

# ── 1) 변수 10개 ──
VARS = [("LedgeFootAnchorL", "struct:Vector"), ("LedgeFootAnchorR", "struct:Vector"),
        ("LedgeFootMcBaseL", "float"), ("LedgeFootMcBaseR", "float"),
        ("LedgeFootWorldL", "struct:Vector"), ("LedgeFootWorldR", "struct:Vector"),
        ("LedgeFootIdleCompL", "struct:Vector"), ("LedgeFootIdleCompR", "struct:Vector"),
        ("LedgeFootIKAlphaL", "float"), ("LedgeFootIKAlphaR", "float")]
existing_vars = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": ABP}).get("variables", [])}
for name, typ in VARS:
    if name in existing_vars:
        LOG["steps"].append("var exists: " + name)
        continue
    call("blueprint_query", "add_variable",
         {"asset_path": ABP, "name": name, "type": typ, "category": "Ledge|FootIK", "instance_editable": False})
    LOG["steps"].append("var added: " + name)

# ── 2) 노드 스펙 (L/R 미러) ──
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


SH = {"off167": "K2Node_CallFunction_167", "off199": "K2Node_CallFunction_199",
      "relatch": "K2Node_CallFunction_220", "stop": "K2Node_CallFunction_161",
      "dt": "K2Node_CallFunction_123", "comp": "K2Node_CallFunction_113",
      "m2w": "K2Node_VariableGet_72", "m2w2": "K2Node_VariableGet_42",
      "fb": "K2Node_VariableGet_71"}

for side in ("L", "R"):
    lo = side.lower()
    yb = 2000 if side == "L" else 3000
    p = lambda s: "f%s_%s" % (side, s)
    # 월드나우(Idle 상수 변환)
    N(p("wn"), "CallFunction", 5000, yb, function_name="TransformLocation", target_class=KML)
    D(p("wn"), "Location", CONST[side])
    C(SH["m2w"], "LedgeMeshToWorld", p("wn"), "T")
    # 앵커 래치
    N(p("g_anchor"), "VariableGet", 5000, yb + 120, variable_name="LedgeFootAnchor" + side)
    N(p("asub"), "CallFunction", 5250, yb, function_name="Subtract_VectorVector", target_class=KML)
    C(p("wn"), "ReturnValue", p("asub"), "A")
    C(SH["off199"], "ReturnValue", p("asub"), "B")
    N(p("asel"), "CallFunction", 5500, yb, function_name="SelectVector", target_class=KML)
    C(p("asub"), "ReturnValue", p("asel"), "A")
    C(p("g_anchor"), "LedgeFootAnchor" + side, p("asel"), "B")
    C(SH["relatch"], "ReturnValue", p("asel"), "bPickA")
    N(p("set_anchor"), "VariableSet", 5750, yb, variable_name="LedgeFootAnchor" + side)
    C(p("asel"), "ReturnValue", p("set_anchor"), "LedgeFootAnchor" + side)
    # 도착지 라이브
    N(p("dest"), "CallFunction", 5250, yb + 220, function_name="Add_VectorVector", target_class=KML)
    C(p("wn"), "ReturnValue", p("dest"), "A")
    C(SH["off167"], "ReturnValue", p("dest"), "B")
    # 무브커브 + McBase 리베이스
    N(p("mcv"), "CallFunction", 5000, yb + 340, function_name="GetCurveValue", target_class="AnimInstance")
    D(p("mcv"), "CurveName", "ledge_foot_move_" + lo)
    N(p("mcc"), "CallFunction", 5200, yb + 340, function_name="FClamp", target_class=KML)
    C(p("mcv"), "ReturnValue", p("mcc"), "Value")
    N(p("g_mcb"), "VariableGet", 5200, yb + 460, variable_name="LedgeFootMcBase" + side)
    N(p("mcbsel"), "CallFunction", 5450, yb + 340, function_name="SelectFloat", target_class=KML)
    C(p("mcc"), "ReturnValue", p("mcbsel"), "A")
    C(p("g_mcb"), "LedgeFootMcBase" + side, p("mcbsel"), "B")
    C(SH["relatch"], "ReturnValue", p("mcbsel"), "bPickA")
    N(p("set_mcb"), "VariableSet", 5700, yb + 340, variable_name="LedgeFootMcBase" + side)
    C(p("mcbsel"), "ReturnValue", p("set_mcb"), "LedgeFootMcBase" + side)
    N(p("num"), "CallFunction", 5450, yb + 460, function_name="Subtract_DoubleDouble", target_class=KML)
    C(p("mcc"), "ReturnValue", p("num"), "A")
    C(p("g_mcb"), "LedgeFootMcBase" + side, p("num"), "B")
    N(p("den"), "CallFunction", 5450, yb + 560, function_name="Subtract_DoubleDouble", target_class=KML)
    D(p("den"), "A", "1.0")
    C(p("g_mcb"), "LedgeFootMcBase" + side, p("den"), "B")
    N(p("denmax"), "CallFunction", 5650, yb + 560, function_name="FMax", target_class=KML)
    C(p("den"), "ReturnValue", p("denmax"), "A")
    D(p("denmax"), "B", "0.05")
    N(p("div"), "CallFunction", 5850, yb + 460, function_name="Divide_DoubleDouble", target_class=KML)
    C(p("num"), "ReturnValue", p("div"), "A")
    C(p("denmax"), "ReturnValue", p("div"), "B")
    N(p("mcadj"), "CallFunction", 6050, yb + 460, function_name="FClamp", target_class=KML)
    C(p("div"), "ReturnValue", p("mcadj"), "Value")
    # 안무 VLerp + 정지수렴 + Z보존
    N(p("vlerp"), "CallFunction", 6250, yb + 220, function_name="VLerp", target_class=KML)
    C(p("g_anchor"), "LedgeFootAnchor" + side, p("vlerp"), "A")
    C(p("dest"), "ReturnValue", p("vlerp"), "B")
    C(p("mcadj"), "ReturnValue", p("vlerp"), "Alpha")
    N(p("stopsel"), "CallFunction", 6450, yb + 220, function_name="SelectVector", target_class=KML)
    C(p("wn"), "ReturnValue", p("stopsel"), "A")
    C(p("vlerp"), "ReturnValue", p("stopsel"), "B")
    C(SH["stop"], "ReturnValue", p("stopsel"), "bPickA")
    N(p("bk1"), "CallFunction", 6650, yb + 220, function_name="BreakVector", target_class=KML)
    C(p("stopsel"), "ReturnValue", p("bk1"), "InVec")
    N(p("bk2"), "CallFunction", 6650, yb + 340, function_name="BreakVector", target_class=KML)
    C(p("wn"), "ReturnValue", p("bk2"), "InVec")
    N(p("mk"), "CallFunction", 6850, yb + 220, function_name="MakeVector", target_class=KML)
    C(p("bk1"), "X", p("mk"), "X")
    C(p("bk1"), "Y", p("mk"), "Y")
    C(p("bk2"), "Z", p("mk"), "Z")
    # 신전 클램프 (thigh 기준 76)
    N(p("sock"), "CallFunction", 6850, yb + 400, function_name="GetSocketLocation", target_class="SceneComponent")
    D(p("sock"), "InSocketName", "thigh_" + lo)
    C(SH["comp"], "ReturnValue", p("sock"), "self")
    N(p("rel"), "CallFunction", 7050, yb + 220, function_name="Subtract_VectorVector", target_class=KML)
    C(p("mk"), "ReturnValue", p("rel"), "A")
    C(p("sock"), "ReturnValue", p("rel"), "B")
    N(p("len"), "CallFunction", 7250, yb + 300, function_name="VSize", target_class=KML)
    C(p("rel"), "ReturnValue", p("len"), "A")
    N(p("mn"), "CallFunction", 7450, yb + 300, function_name="FMin", target_class=KML)
    C(p("len"), "ReturnValue", p("mn"), "A")
    D(p("mn"), "B", "76.0")
    N(p("nrm"), "CallFunction", 7250, yb + 180, function_name="Normal", target_class=KML)
    C(p("rel"), "ReturnValue", p("nrm"), "A")
    N(p("scaled"), "CallFunction", 7650, yb + 220, function_name="Multiply_VectorFloat", target_class=KML)
    C(p("nrm"), "ReturnValue", p("scaled"), "A")
    C(p("mn"), "ReturnValue", p("scaled"), "B")
    N(p("eff"), "CallFunction", 7850, yb + 220, function_name="Add_VectorVector", target_class=KML)
    C(p("sock"), "ReturnValue", p("eff"), "A")
    C(p("scaled"), "ReturnValue", p("eff"), "B")
    # VInterp + Set World / IdleComp
    N(p("g_fw"), "VariableGet", 7850, yb + 360, variable_name="LedgeFootWorld" + side)
    N(p("vint"), "CallFunction", 8050, yb + 220, function_name="VInterpTo", target_class=KML)
    C(p("g_fw"), "LedgeFootWorld" + side, p("vint"), "Current")
    C(p("eff"), "ReturnValue", p("vint"), "Target")
    C(SH["dt"], "ReturnValue", p("vint"), "DeltaTime")
    D(p("vint"), "InterpSpeed", "14.0")
    N(p("set_fw"), "VariableSet", 8250, yb + 220, variable_name="LedgeFootWorld" + side)
    C(p("vint"), "ReturnValue", p("set_fw"), "LedgeFootWorld" + side)
    N(p("inv"), "CallFunction", 8450, yb + 220, function_name="InverseTransformLocation", target_class=KML)
    C(SH["m2w2"], "LedgeMeshToWorld", p("inv"), "T")
    C(p("g_fw"), "LedgeFootWorld" + side, p("inv"), "Location")
    N(p("set_comp"), "VariableSet", 8650, yb + 220, variable_name="LedgeFootIdleComp" + side)
    C(p("inv"), "ReturnValue", p("set_comp"), "LedgeFootIdleComp" + side)
    # 알파: ik커브 × FrontBlocked → FInterp
    N(p("av"), "CallFunction", 8050, yb + 500, function_name="GetCurveValue", target_class="AnimInstance")
    D(p("av"), "CurveName", "ledge_foot_ik_" + lo)
    N(p("avc"), "CallFunction", 8250, yb + 500, function_name="FClamp", target_class=KML)
    C(p("av"), "ReturnValue", p("avc"), "Value")
    N(p("gate"), "CallFunction", 8450, yb + 500, function_name="SelectFloat", target_class=KML)
    C(p("avc"), "ReturnValue", p("gate"), "A")
    D(p("gate"), "B", "0.0")
    C(SH["fb"], "LedgeFrontBlocked", p("gate"), "bPickA")
    N(p("g_alpha"), "VariableGet", 8450, yb + 620, variable_name="LedgeFootIKAlpha" + side)
    N(p("fint"), "CallFunction", 8650, yb + 500, function_name="FInterpTo", target_class=KML)
    C(p("g_alpha"), "LedgeFootIKAlpha" + side, p("fint"), "Current")
    C(p("gate"), "ReturnValue", p("fint"), "Target")
    C(SH["dt"], "ReturnValue", p("fint"), "DeltaTime")
    D(p("fint"), "InterpSpeed", "15.0")
    N(p("set_alpha"), "VariableSet", 8850, yb + 500, variable_name="LedgeFootIKAlpha" + side)
    C(p("fint"), "ReturnValue", p("set_alpha"), "LedgeFootIKAlpha" + side)

# ── 3) 노드 생성 ──
res = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": G, "nodes": nodes})
LOG["add_nodes_raw"] = res
tmap = {}
def harvest(obj):
    if isinstance(obj, dict):
        if obj.get("temp_id") and (obj.get("node_id") or obj.get("id")):
            tmap[obj["temp_id"]] = obj.get("node_id") or obj.get("id")
        else:
            for k, v in obj.items():
                if isinstance(v, str) and k.startswith("f") and "_" in k:
                    tmap[k] = v
                else:
                    harvest(v)
    elif isinstance(obj, list):
        for e in obj:
            harvest(e)
harvest(res)
bad = [t for t, v in tmap.items() if not v]
if len(tmap) != len(nodes) or bad:
    LOG["errors"].append("node create mismatch: %d/%d bad=%s" % (len(tmap), len(nodes), bad[:10]))
LOG["steps"].append("nodes created: %d" % len(tmap))

# ── 4) 디폴트 ──
for d in defaults:
    d["node_id"] = tmap.get(d["node_id"], d["node_id"])
rd = call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": ABP, "graph_name": G, "defaults": defaults})
LOG["defaults_result"] = rd

# ── 5) 데이터 연결 ──
for c in conns:
    c["source_node"] = tmap.get(c["source_node"], c["source_node"])
    c["target_node"] = tmap.get(c["target_node"], c["target_node"])
rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": G, "connections": conns})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
LOG["conn_fail"] = fails
LOG["steps"].append("data links: %d req, %d fail" % (len(conns), len(fails)))

# ── 6) exec 스플라이스 ──
# 6a: VS_34 → [발 앵커/맥베이스 4개] → VS_29 (DestTd 갱신 전에 래치 평가)
call("blueprint_query", "disconnect_pins",
     {"asset_path": ABP, "graph_name": G, "node_id": "K2Node_VariableSet_34", "pin_name": "then"})
ex = []
chain_a = ["K2Node_VariableSet_34", tmap["fL_set_anchor"], tmap["fR_set_anchor"],
           tmap["fL_set_mcb"], tmap["fR_set_mcb"], "K2Node_VariableSet_29"]
for i in range(len(chain_a) - 1):
    ex.append({"source_node": chain_a[i], "source_pin": "then", "target_node": chain_a[i + 1], "target_pin": "execute"})
ex[0]["source_pin"] = "then"
# 6b: VS_1(꼬리) → 발 World/IdleComp/Alpha 6개
chain_b = ["K2Node_VariableSet_1", tmap["fL_set_fw"], tmap["fR_set_fw"],
           tmap["fL_set_comp"], tmap["fR_set_comp"], tmap["fL_set_alpha"], tmap["fR_set_alpha"]]
for i in range(len(chain_b) - 1):
    ex.append({"source_node": chain_b[i], "source_pin": "then", "target_node": chain_b[i + 1], "target_pin": "execute"})
re_ = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": G, "connections": ex})
exfails = [x for x in (re_.get("results") or []) if not x.get("success", True)]
LOG["exec_fail"] = exfails
LOG["steps"].append("exec links: %d req, %d fail" % (len(ex), len(exfails)))
LOG["tmap"] = tmap

with open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/foot_build.json", "w") as fp:
    json.dump(LOG, fp, indent=1, ensure_ascii=False)
print("FOOT_BUILD_DONE steps=%s errors=%s conn_fail=%d exec_fail=%d" %
      (len(LOG["steps"]), LOG["errors"], len(fails), len(exfails)))
