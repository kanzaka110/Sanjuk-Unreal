# slope_z_m1_hands.py apply 중단 재개 (IsValid 핀명 Object 수정) — 노드 생성 완료 후 배선부터
# 실행: py slope_z_m1b_resume.py apply
import json, sys, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GH = "Ledge_HandTarget"
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"

MADE = {
    "getSp": "K2Node_VariableGet_15", "isv": "K2Node_CallFunction_36", "br": "K2Node_IfThenElse_5",
    "fcl": "K2Node_CallFunction_42", "bkCL": "K2Node_CallFunction_139", "bkWL": "K2Node_CallFunction_140",
    "addL": "K2Node_CallFunction_141", "subL": "K2Node_CallFunction_142",
    "fcr": "K2Node_CallFunction_157", "bkCR": "K2Node_CallFunction_158", "bkWR": "K2Node_CallFunction_179",
    "addR": "K2Node_CallFunction_180", "subR": "K2Node_CallFunction_181",
    "addB": "K2Node_CallFunction_182", "mulB": "K2Node_CallFunction_183",
    "setL": "K2Node_VariableSet_15", "setR": "K2Node_VariableSet_16", "setB": "K2Node_VariableSet_19",
    "setL0": "K2Node_VariableSet_22", "setR0": "K2Node_VariableSet_23", "setB0": "K2Node_VariableSet_24",
    "getL": "K2Node_VariableGet_50", "mkL": "K2Node_CallFunction_187", "avL": "K2Node_CallFunction_188",
    "getR": "K2Node_VariableGet_61", "mkR": "K2Node_CallFunction_189", "avR": "K2Node_CallFunction_190",
}
WNL, WNR = "K2Node_CallFunction_55", "K2Node_CallFunction_91"
VIL, VIR = "K2Node_CallFunction_115", "K2Node_CallFunction_177"
UP_NODE, UP_PIN = "K2Node_VariableSet_3", "then"
M4BR = "K2Node_IfThenElse_4"


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


def graph(g):
    return {n["id"]: n for n in bq("get_graph_data", {"graph_name": g})["nodes"]}


def pins(nodes, nid):
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


# 사전 확인: 노드 실재
nodes = graph(GH)
missing = [k for k, v in MADE.items() if v not in nodes]
assert not missing, "노드 미발견: " + json.dumps(missing)
print("[PF] 노드 28종 실재 OK")

if not APPLY:
    print("== dry-run 종료 ==")
    sys.exit(0)


def wire(sk, sp, tk, tp):
    src = MADE.get(sk, sk)
    tgt = MADE.get(tk, tk)
    bq("connect_pins", {"graph_name": GH, "source_node": src, "source_pin": sp,
                        "target_node": tgt, "target_pin": tp})
    print("[WIRE]", sk + "." + sp, "->", tk + "." + tp)


def cut(sk, sp, tk, tp):
    bq("disconnect_pins", {"graph_name": GH, "source_node": MADE.get(sk, sk), "source_pin": sp,
                           "target_node": MADE.get(tk, tk), "target_pin": tp})
    print("[CUT]", sk + "." + sp, "-X->", tk + "." + tp)


# 게이트 조건 (IsValid 핀명 = Object)
wire("getSp", "LedgeSplineRef", "isv", "Object")
wire("isv", "ReturnValue", "br", "Condition")
# L 데이터
wire("getSp", "LedgeSplineRef", "fcl", "self")
wire(WNL, "ReturnValue", "fcl", "WorldLocation")
wire("fcl", "ReturnValue", "bkCL", "InVec")
wire(WNL, "ReturnValue", "bkWL", "InVec")
wire("bkCL", "Z", "addL", "A")
wire("addL", "ReturnValue", "subL", "A")
wire("bkWL", "Z", "subL", "B")
wire("subL", "ReturnValue", "setL", "LedgeSlopeDzL")
# R 데이터
wire("getSp", "LedgeSplineRef", "fcr", "self")
wire(WNR, "ReturnValue", "fcr", "WorldLocation")
wire("fcr", "ReturnValue", "bkCR", "InVec")
wire(WNR, "ReturnValue", "bkWR", "InVec")
wire("bkCR", "Z", "addR", "A")
wire("addR", "ReturnValue", "subR", "A")
wire("bkWR", "Z", "subR", "B")
wire("subR", "ReturnValue", "setR", "LedgeSlopeDzR")
# Body 평균
wire("subL", "ReturnValue", "addB", "A")
wire("subR", "ReturnValue", "addB", "B")
wire("addB", "ReturnValue", "mulB", "A")
wire("mulB", "ReturnValue", "setB", "LedgeSlopeDzBody")
# exec 스플라이스
cut(UP_NODE, UP_PIN, M4BR, "execute")
wire(UP_NODE, UP_PIN, "br", "execute")
wire("br", "then", "setL", "execute")
wire("setL", "then", "setR", "execute")
wire("setR", "then", "setB", "execute")
wire("setB", "then", M4BR, "execute")
wire("br", "else", "setL0", "execute")
wire("setL0", "then", "setR0", "execute")
wire("setR0", "then", "setB0", "execute")
wire("setB0", "then", M4BR, "execute")
# 소비: VInterp.Target 재배선
wire("getL", "LedgeSlopeDzL", "mkL", "Z")
wire(WNL, "ReturnValue", "avL", "A")
wire("mkL", "ReturnValue", "avL", "B")
cut(WNL, "ReturnValue", VIL, "Target")
wire("avL", "ReturnValue", VIL, "Target")
wire("getR", "LedgeSlopeDzR", "mkR", "Z")
wire(WNR, "ReturnValue", "avR", "A")
wire("mkR", "ReturnValue", "avR", "B")
cut(WNR, "ReturnValue", VIR, "Target")
wire("avR", "ReturnValue", VIR, "Target")

# ══ 검증 ══
nodes2 = graph(GH)


def haslink(sn, sp, tn, tp):
    pm = pins(nodes2, MADE.get(tn, tn))
    return any(c == MADE.get(sn, sn) + "." + sp for c in pm.get(tp, {}).get("connected_to", []))


checks = [
    ("getSp", "LedgeSplineRef", "isv", "Object"),
    ("isv", "ReturnValue", "br", "Condition"),
    (WNL, "ReturnValue", "fcl", "WorldLocation"),
    ("fcl", "ReturnValue", "bkCL", "InVec"),
    ("subL", "ReturnValue", "setL", "LedgeSlopeDzL"),
    (WNR, "ReturnValue", "fcr", "WorldLocation"),
    ("subR", "ReturnValue", "setR", "LedgeSlopeDzR"),
    ("mulB", "ReturnValue", "setB", "LedgeSlopeDzBody"),
    ("avL", "ReturnValue", VIL, "Target"),
    ("avR", "ReturnValue", VIR, "Target"),
    (UP_NODE, UP_PIN, "br", "execute"),
    ("br", "then", "setL", "execute"),
    ("setB", "then", M4BR, "execute"),
    ("br", "else", "setL0", "execute"),
    ("setB0", "then", M4BR, "execute"),
]
ok = True
for c in checks:
    good = haslink(*c)
    ok = ok and good
    print("[CHK]", ("OK " if good else "FAIL"), c[0] + "." + c[1], "->", c[2] + "." + c[3])
for side, VI in (("L", VIL), ("R", VIR)):
    tgt_srcs = pins(nodes2, VI)["Target"]["connected_to"]
    good = tgt_srcs == [MADE["av" + side] + ".ReturnValue"]
    ok = ok and good
    print("[CHK]", ("OK " if good else "FAIL"), "VInterp" + side + ".Target =", tgt_srcs)
assert ok, "링크 검증 실패"

r = bq("compile_blueprint", {})
print("[COMPILE]", json.dumps(r)[:300])
