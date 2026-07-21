# 발 타깃 1프레임 외삽 (2026-07-21) — ball 접지 지연 보정
#
# 실측 근거 (probe_ankle.py, 알파>=0.95 n=1275/1269):
#   L: ball오차 = 0.81 x 타깃이동량 + 1.5   /   R: ball오차 = 1.00 x 타깃이동량 + 2.0
#   기울기 ~1.0 = IK가 "못 따라가는" 게 아니라 딱 1샘플 뒤처진 위치를 정확히 따라간다.
#   원인: ABP UpdateVariables 는 애님 평가 '전'에 돌고 거기서 읽는 소켓이 전프레임 포즈.
#
# 처방:  predicted = world + Clamp((world - prevWorld) * K, MAXLEAD)
#        CF_27/57(InverseTransformLocation).Location 을 predicted 로 교체.
#        LedgeFootWorld 자체는 그대로 둔다 (다른 소비자/디버그 호환).
#
# ⚠ SetPrev 는 반드시 IdleComp(VS_3/VS_8) '뒤' — 앞에 두면 같은 프레임에 Prev 가 갱신돼 lead=0.
# 백업: foottarget_dump.json (127노드)
import json, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
FT = "Ledge_FootTarget"
KML = "KismetMathLibrary"
K = 0.8          # 실측 기울기 0.81~1.00 → 과보정(급정지 오버슈트) 회피로 0.8
MAXLEAD = 10.0   # 외삽 상한 cm
LOG = {"steps": [], "errors": []}

# 삽입 지점 (foottarget_dump.json 실측)
INV = {"L": "K2Node_CallFunction_27", "R": "K2Node_CallFunction_57"}
WORLD_SET = {"L": "K2Node_VariableSet_2", "R": "K2Node_VariableSet_7"}
COMP_SET = {"L": "K2Node_VariableSet_3", "R": "K2Node_VariableSet_8"}
AFTER_COMP = "K2Node_VariableSet_4"   # Set LedgeFootIKAlphaL (VS_8 의 기존 then 대상)


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


# ── 0) 사전 검증: 삽입 지점이 덤프와 같은 모습인지 (K2Node ID 재할당 방어) ──
g = call("blueprint_query", "get_graph_data", {"asset_path": ABP, "graph_name": FT})
nodes = {n["id"]: n for n in g["nodes"]}


def pin(nid, pname):
    for p in nodes.get(nid, {}).get("pins", []):
        if p["name"] == pname:
            return p
    return None


for s in ("L", "R"):
    if INV[s] not in nodes or "Inverse Transform Location" not in nodes[INV[s]].get("title", ""):
        raise SystemExit("앵커 불일치(Inverse Transform): " + INV[s])
    src = (pin(INV[s], "Location") or {}).get("connected_to") or []
    if not src or "LedgeFootWorld" not in src[0]:
        raise SystemExit("%s Location 소스가 예상과 다름: %s" % (INV[s], src))
if (pin(COMP_SET["R"], "then") or {}).get("connected_to") != [AFTER_COMP + ".execute"]:
    raise SystemExit("VS_8 then 대상 불일치: %s" % (pin(COMP_SET["R"], "then") or {}).get("connected_to"))
LOG["steps"].append("anchors verified")

# ── 1) 변수 4개 ──
existing = {v["name"] for v in call("blueprint_query", "get_variables", {"asset_path": ABP}).get("variables", [])}
for s in ("L", "R"):
    for nm in ("LedgePrevFootWorld" + s, "LedgeFootWorldPred" + s):
        if nm not in existing:
            call("blueprint_query", "add_variable",
                 {"asset_path": ABP, "name": nm, "type": "struct:Vector",
                  "category": "Ledge|FootIK", "instance_editable": False})
            LOG["steps"].append("var added: " + nm)

# ── 2) 노드 생성 ──
nodes_spec, conns, defaults = [], [], []


def N(tid, ntype, x, y, **kw):
    d = {"temp_id": tid, "node_type": ntype, "position": [x, y]}
    d.update(kw)
    nodes_spec.append(d)


def C(sn, sp, tn, tp):
    conns.append({"source_node": sn, "source_pin": sp, "target_node": tn, "target_pin": tp})


for s in ("L", "R"):
    yb = 2600 if s == "L" else 3000
    p = lambda k: "lead%s_%s" % (s, k)
    N(p("gw"), "VariableGet", 3400, yb, variable_name="LedgeFootWorld" + s)
    N(p("gp"), "VariableGet", 3400, yb + 100, variable_name="LedgePrevFootWorld" + s)
    N(p("sub"), "CallFunction", 3650, yb, function_name="Subtract_VectorVector", target_class=KML)
    N(p("mul"), "CallFunction", 3850, yb, function_name="Multiply_VectorFloat", target_class=KML)
    N(p("clm"), "CallFunction", 4050, yb, function_name="ClampVectorSize", target_class=KML)
    N(p("add"), "CallFunction", 4250, yb, function_name="Add_VectorVector", target_class=KML)
    N(p("spred"), "VariableSet", 4450, yb, variable_name="LedgeFootWorldPred" + s)
    N(p("sprev"), "VariableSet", 4450, yb + 160, variable_name="LedgePrevFootWorld" + s)

res = call("blueprint_query", "add_nodes_bulk", {"asset_path": ABP, "graph_name": FT, "nodes": nodes_spec})
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
if len(tmap) != len(nodes_spec):
    raise SystemExit("노드 생성 불일치 %d/%d: %s" % (len(tmap), len(nodes_spec), json.dumps(res)[:300]))
LOG["steps"].append("nodes created: %d" % len(tmap))

# ── 3) 핀 디폴트 (K / 상한) ──
for s in ("L", "R"):
    p = lambda k: tmap["lead%s_%s" % (s, k)]
    defaults.append({"node_id": p("mul"), "pin_name": "B", "value": str(K)})
    defaults.append({"node_id": p("clm"), "pin_name": "Max", "value": str(MAXLEAD)})
call("blueprint_query", "set_pin_defaults_bulk", {"asset_path": ABP, "graph_name": FT, "defaults": defaults})

# ── 4) 데이터 배선 ──
for s in ("L", "R"):
    t = lambda k: tmap["lead%s_%s" % (s, k)]
    C(t("gw"), "LedgeFootWorld" + s, t("sub"), "A")
    C(t("gp"), "LedgePrevFootWorld" + s, t("sub"), "B")
    C(t("sub"), "ReturnValue", t("mul"), "A")
    C(t("mul"), "ReturnValue", t("clm"), "A")
    C(t("gw"), "LedgeFootWorld" + s, t("add"), "A")
    C(t("clm"), "ReturnValue", t("add"), "B")
    C(t("add"), "ReturnValue", t("spred"), "LedgeFootWorldPred" + s)
    C(t("gw"), "LedgeFootWorld" + s, t("sprev"), "LedgePrevFootWorld" + s)
    # 핵심: IdleComp 계산 입력을 외삽값으로 교체
    call("blueprint_query", "disconnect_pins",
         {"asset_path": ABP, "graph_name": FT, "node_id": INV[s], "pin_name": "Location"})
    C(t("add"), "ReturnValue", INV[s], "Location")

# ── 5) exec 스플라이스 ──
#   WorldR -> SetPredL -> SetPredR -> IdleCompL -> IdleCompR -> SetPrevL -> SetPrevR -> AlphaL
call("blueprint_query", "disconnect_pins",
     {"asset_path": ABP, "graph_name": FT, "node_id": WORLD_SET["R"], "pin_name": "then"})
call("blueprint_query", "disconnect_pins",
     {"asset_path": ABP, "graph_name": FT, "node_id": COMP_SET["R"], "pin_name": "then"})
chain = [WORLD_SET["R"], tmap["leadL_spred"], tmap["leadR_spred"], COMP_SET["L"], COMP_SET["R"],
         tmap["leadL_sprev"], tmap["leadR_sprev"], AFTER_COMP]
for a, b in zip(chain, chain[1:]):
    C(a, "then", b, "execute")

rc = call("blueprint_query", "connect_pins_bulk", {"asset_path": ABP, "graph_name": FT, "connections": conns})
fails = [x for x in (rc.get("results") or []) if not x.get("success", True)]
if fails:
    LOG["errors"].append({"conn_fails": fails})
LOG["steps"].append("links: %d (%d fails)" % (len(conns), len(fails)))

json.dump(LOG, open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/foot_lead.json", "w"), indent=1, ensure_ascii=False)
print("FOOT_LEAD_DONE fails=%d" % len(LOG["errors"]))
for s in LOG["steps"]:
    print("  " + s)
