# Phase C M4 — None 안전성 (2026-07-23)
# 런타임 오류 실측 2종:
#   A) Td에지(콜리전off) 빈 배열에 Array_Get(0/1)/GetComponentByClass 평가 → 워닝 스팸
#   B) SplineRef None 구간에도 SelectVector 양핀 평가 → GetTransformAtDistance(None)
# 수정:
#   A) 래치 체인: Array_Length>0 Branch 게이트 + get1.Index=SelectInt(len>1?1:0) + setT 앞 IsValid 게이트
#   B) 슬라이드 타깃을 exec 게이트(Branch: IsValid(SplineRef) AND sd≠td) 안에서 변수(LedgeSlideTgt**)로
#      Set — Set LedgeHandWorldL / Set LedgeFootWorldL 직전 스플라이스 (알파/McBase 신선도 보장).
#      소비 Select B핀은 변수 Get으로 교체, bPickA에 OR(NOT IsValid) 추가
# 실행: py phase_c_m4_nullsafe.py [apply]
import json, sys, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GH = "Ledge_HandTarget"
GF = "Ledge_FootTarget"
KML = "KismetMathLibrary"
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"

VS6 = "K2Node_VariableSet_6"
BRV = "K2Node_IfThenElse_1"    # IsValid(ssel) Branch (M1b)
BRT = "K2Node_IfThenElse_0"    # Td에지 Branch
SETSD = "K2Node_VariableSet_10"
SETTD = "K2Node_VariableSet_11"
SETT = "K2Node_VariableSet_12"
OV = "K2Node_CallFunction_34"      # GetOverlappingActors
GET1 = "K2Node_CallArrayFunction_1"
TL_HL = "K2Node_CallFunction_120"  # TransformLocation L (M2)
TL_HR = "K2Node_CallFunction_137"
SEL_HL = "K2Node_CallFunction_121"
SEL_HR = "K2Node_CallFunction_138"
OR_H = "K2Node_CallFunction_156"   # OR(TransitActive, eq) (M3)
TL_FL = "K2Node_CallFunction_89"
TL_FR = "K2Node_CallFunction_93"
SEL_FL = "K2Node_CallFunction_15"
SEL_FR = "K2Node_CallFunction_45"


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


def exec_pred(nodes, nid):
    """nid의 execute 입력에 연결된 (노드, 핀) 목록"""
    out = []
    for p in nodes[nid].get("pins", []):
        if p["name"] == "execute" and p["direction"] == "input":
            for c in p.get("connected_to", []):
                out.append(tuple(c.rsplit(".", 1)))
    return out


def find_varset(nodes, varname):
    for nid, n in nodes.items():
        if n["class"] == "K2Node_VariableSet" and any(p["name"] == varname for p in n.get("pins", [])):
            return nid
    return None


hn = graph(GH)
fn = graph(GF)

SETW_HL = find_varset(hn, "LedgeHandWorldL")
SETW_FL = find_varset(fn, "LedgeFootWorldL")
assert SETW_HL and SETW_FL, "Set WorldL 미발견"
pred_h = exec_pred(hn, SETW_HL)
pred_f = exec_pred(fn, SETW_FL)
assert len(pred_h) == 1 and len(pred_f) == 1, "WorldL exec 선행 다중/없음: %s %s" % (pred_h, pred_f)
print("[PF] Set HandWorldL:", SETW_HL, "<-", pred_h[0])
print("[PF] Set FootWorldL:", SETW_FL, "<-", pred_f[0])

def gate_of(nodes, sel):
    """sel.bPickA ← OR ← (…, eq). 반환: (or노드, or핀), eq노드"""
    src = pinsof(nodes, sel)["bPickA"]["connected_to"]
    assert len(src) == 1, sel + " bPickA 소스: " + str(src)
    orn, orp = src[0].rsplit(".", 1)
    eq = None
    for p in nodes[orn].get("pins", []):
        if p["direction"] == "input":
            for c in p.get("connected_to", []):
                cn = c.split(".")[0]
                if nodes.get(cn, {}).get("function") == "EqualEqual_DoubleDouble":
                    eq = cn
    assert eq, sel + " eq 미발견 (or=" + orn + ")"
    return (orn, orp), eq

OR_HL, EQ_H = gate_of(hn, SEL_HL)
OR_HR, _ = gate_of(hn, SEL_HR)
print("[PF] hand gates:", OR_HL, OR_HR, "eq:", EQ_H)
OR_FL, EQ_F = gate_of(fn, SEL_FL)
OR_FR, _ = gate_of(fn, SEL_FR)
print("[PF] foot gates:", OR_FL, OR_FR, "eq:", EQ_F)
# B핀 실소스 (경유 노드 대응)
def b_src(nodes, sel):
    s = pinsof(nodes, sel)["B"]["connected_to"]
    assert len(s) == 1, sel + ".B 소스: " + str(s)
    return tuple(s[0].rsplit(".", 1))

BS_HL, BS_HR = b_src(hn, SEL_HL), b_src(hn, SEL_HR)
BS_FL, BS_FR = b_src(fn, SEL_FL), b_src(fn, SEL_FR)
print("[PF] B srcs:", BS_HL, BS_HR, BS_FL, BS_FR)
assert pinsof(hn, SETTD)["then"]["connected_to"] == [SETT + ".execute"], "setTd.then 상이"
assert pinsof(hn, VS6)["then"]["connected_to"] == [BRV + ".execute"], "VS6.then 상이"

if not APPLY:
    print("== DRY-RUN OK ==")
    sys.exit(0)

assert not pie_on(), "PIE 실행 중 — 종료 후 apply"
for g in (GH, GF):
    exp = bq("export_graph", {"graph_name": g})
    with open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/phaseC_m4_backup_%s.json" % g, "w", encoding="utf-8") as f:
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


def arr_fn(g, member, pos):
    nid = add(g, "CallArrayFunction", {}, pos)
    bq("set_node_property", {"graph_name": g, "node_id": nid, "property_name": "FunctionReference",
        "value": "(MemberParent=\"/Script/CoreUObject.Class'/Script/Engine.KismetArrayLibrary'\",MemberName=\"%s\")" % member})
    return nid


# ══ 신규 변수 ══
vars_d = bq("get_variables", {})
vnames = {v["name"] for v in vars_d["variables"]}
for name in ("LedgeSlideTgtHL", "LedgeSlideTgtHR", "LedgeSlideTgtFL", "LedgeSlideTgtFR"):
    if name not in vnames:
        bq("add_variable", {"name": name, "type": "struct:Vector", "category": "Ledge|PhaseC"})
        print("[VAR] +", name)

# ══ A) 래치 체인 길이 가드 (GH) ══
X, Y = -5000, 3000
alen = arr_fn(GH, "Array_Length", [X, Y])
wire(GH, OV, "OverlappingActors", alen, "TargetArray")
gr0 = add(GH, "CallFunction", {"function_class": KML, "function_name": "Greater_IntInt"}, [X + 220, Y])
wire(GH, alen, "ReturnValue", gr0, "A")
bq("set_pin_default", {"graph_name": GH, "node_id": gr0, "pin_name": "B", "value": "0"})
gr1 = add(GH, "CallFunction", {"function_class": KML, "function_name": "Greater_IntInt"}, [X + 220, Y + 100])
wire(GH, alen, "ReturnValue", gr1, "A")
bq("set_pin_default", {"graph_name": GH, "node_id": gr1, "pin_name": "B", "value": "1"})
si1 = add(GH, "CallFunction", {"function_class": KML, "function_name": "SelectInt"}, [X + 420, Y + 100])
bq("set_pin_default", {"graph_name": GH, "node_id": si1, "pin_name": "A", "value": "1"})
bq("set_pin_default", {"graph_name": GH, "node_id": si1, "pin_name": "B", "value": "0"})
wire(GH, gr1, "ReturnValue", si1, "bPickA")
wire(GH, si1, "ReturnValue", GET1, "Index")
brL = add(GH, "Branch", {}, [X + 420, Y - 100])
wire(GH, gr0, "ReturnValue", brL, "Condition")
disc(GH, VS6, "then", BRV, "execute")
wire(GH, VS6, "then", brL, "execute")
wire(GH, brL, "then", BRV, "execute")
wire(GH, brL, "else", BRT, "execute")
# setT 앞 IsValid 게이트
vgs_h = add(GH, "VariableGet", {"variable_name": "LedgeSplineRef"}, [X + 650, Y])
isv_h = add(GH, "CallFunction", {"function_class": "KismetSystemLibrary", "function_name": "IsValid"}, [X + 850, Y])
wire(GH, vgs_h, "LedgeSplineRef", isv_h, "Object")
brV2 = add(GH, "Branch", {}, [X + 1050, Y - 100])
wire(GH, isv_h, "ReturnValue", brV2, "Condition")
disc(GH, SETTD, "then", SETT, "execute")
wire(GH, SETTD, "then", brV2, "execute")
wire(GH, brV2, "then", SETT, "execute")
# brV2.else → setT의 원래 후속(NEXT)으로
sett_then = pinsof(graph(GH), SETT)["then"]["connected_to"][0].rsplit(".", 1)
wire(GH, brV2, "else", sett_then[0], sett_then[1])
print("[A] 래치 길이가드 + setT IsValid 게이트 완료")


def slide_gate(g, eq_node, tlL, tlR, varL, varR, setw, predw, selL, selR, orL, orR, bsL, bsR, pos):
    X, Y = pos
    vgs = add(g, "VariableGet", {"variable_name": "LedgeSplineRef"}, [X, Y])
    isv = add(g, "CallFunction", {"function_class": "KismetSystemLibrary", "function_name": "IsValid"}, [X + 200, Y])
    wire(g, vgs, "LedgeSplineRef", isv, "Object")
    ne = add(g, "CallFunction", {"function_class": KML, "function_name": "Not_PreBool"}, [X + 200, Y + 80])
    wire(g, eq_node, "ReturnValue", ne, "A")
    an = add(g, "CallFunction", {"function_class": KML, "function_name": "BooleanAND"}, [X + 400, Y])
    wire(g, isv, "ReturnValue", an, "A")
    wire(g, ne, "ReturnValue", an, "B")
    brS = add(g, "Branch", {}, [X + 600, Y - 120])
    wire(g, an, "ReturnValue", brS, "Condition")
    sL = add(g, "VariableSet", {"variable_name": varL}, [X + 850, Y - 120])
    sR = add(g, "VariableSet", {"variable_name": varR}, [X + 1100, Y - 120])
    wire(g, tlL, "ReturnValue", sL, varL)
    wire(g, tlR, "ReturnValue", sR, varR)
    # 스플라이스: predw → brS → (then sL→sR→setw / else setw)
    disc(g, predw[0], predw[1], setw, "execute")
    wire(g, predw[0], predw[1], brS, "execute")
    wire(g, brS, "then", sL, "execute")
    wire(g, sL, "then", sR, "execute")
    wire(g, sR, "then", setw, "execute")
    wire(g, brS, "else", setw, "execute")
    # 소비 교체
    gvL = add(g, "VariableGet", {"variable_name": varL}, [X + 850, Y + 150])
    gvR = add(g, "VariableGet", {"variable_name": varR}, [X + 1100, Y + 150])
    disc(g, bsL[0], bsL[1], selL, "B")
    disc(g, bsR[0], bsR[1], selR, "B")
    wire(g, gvL, varL, selL, "B")
    wire(g, gvR, varR, selR, "B")
    # bPickA 폴백 확장: OR(기존, NOT IsValid)
    inv = add(g, "CallFunction", {"function_class": KML, "function_name": "Not_PreBool"}, [X + 400, Y + 220])
    wire(g, isv, "ReturnValue", inv, "A")
    for sel, orsrc in ((selL, orL), (selR, orR)):
        o2 = add(g, "CallFunction", {"function_class": KML, "function_name": "BooleanOR"}, [X + 600, Y + 220])
        wire(g, orsrc[0], orsrc[1], o2, "A")
        wire(g, inv, "ReturnValue", o2, "B")
        disc(g, orsrc[0], orsrc[1], sel, "bPickA")
        wire(g, o2, "ReturnValue", sel, "bPickA")
    print("[B]", g, "슬라이드 exec 게이트화 완료")


slide_gate(GH, EQ_H, TL_HL, TL_HR, "LedgeSlideTgtHL", "LedgeSlideTgtHR",
           SETW_HL, pred_h[0], SEL_HL, SEL_HR, OR_HL, OR_HR, BS_HL, BS_HR, [-5000, 5600])
slide_gate(GF, EQ_F, TL_FL, TL_FR, "LedgeSlideTgtFL", "LedgeSlideTgtFR",
           SETW_FL, pred_f[0], SEL_FL, SEL_FR, OR_FL, OR_FR, BS_FL, BS_FR, [-3000, 3900])

r = bq("compile_blueprint", {})
print("[COMPILE]", json.dumps(r, ensure_ascii=False)[:200])
