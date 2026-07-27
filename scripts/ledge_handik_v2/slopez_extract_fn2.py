# slopez_extract_fn.py 중단 재개 — dt 노드부터 (GameplayStatics.GetWorldDeltaSeconds)
import json, sys, urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GH = "Ledge_HandTarget"
GF = "Ledge_SlopeZ"
KML = "KismetMathLibrary"
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"

MADE = {"getSp": "K2Node_VariableGet_0", "isv": "K2Node_CallFunction_0", "br": "K2Node_IfThenElse_0",
        "fcL": "K2Node_CallFunction_1", "bkCL": "K2Node_CallFunction_2", "bkWL": "K2Node_CallFunction_3",
        "addL": "K2Node_CallFunction_4", "subL": "K2Node_CallFunction_5", "ndL": "K2Node_CallFunction_6",
        "leL": "K2Node_CallFunction_7", "clL": "K2Node_CallFunction_8", "selL": "K2Node_CallFunction_9",
        "fcR": "K2Node_CallFunction_10", "bkCR": "K2Node_CallFunction_11", "bkWR": "K2Node_CallFunction_12",
        "addR": "K2Node_CallFunction_13", "subR": "K2Node_CallFunction_14", "ndR": "K2Node_CallFunction_15",
        "leR": "K2Node_CallFunction_16", "clR": "K2Node_CallFunction_17", "selR": "K2Node_CallFunction_18",
        "fmax": "K2Node_CallFunction_19", "dsub": "K2Node_CallFunction_20", "dabs": "K2Node_CallFunction_21",
        "mulK": "K2Node_CallFunction_22", "addF": "K2Node_CallFunction_23", "clB": "K2Node_CallFunction_24",
        "getTA": "K2Node_VariableGet_1", "selB": "K2Node_CallFunction_25", "getPrev": "K2Node_VariableGet_2"}
OLD = {
    "br": "K2Node_IfThenElse_5", "isv": "K2Node_CallFunction_36", "getSp": "K2Node_VariableGet_15",
    "fcl": "K2Node_CallFunction_42", "bkCL": "K2Node_CallFunction_139", "bkWL": "K2Node_CallFunction_140",
    "addL": "K2Node_CallFunction_141", "subL": "K2Node_CallFunction_142",
    "fcr": "K2Node_CallFunction_157", "bkCR": "K2Node_CallFunction_158", "bkWR": "K2Node_CallFunction_179",
    "addR": "K2Node_CallFunction_180", "subR": "K2Node_CallFunction_181",
    "setL": "K2Node_VariableSet_15", "setR": "K2Node_VariableSet_16", "setB": "K2Node_VariableSet_19",
    "setL0": "K2Node_VariableSet_22", "setR0": "K2Node_VariableSet_23", "setB0": "K2Node_VariableSet_24",
    "ndL": "K2Node_CallFunction_234", "ndR": "K2Node_CallFunction_235",
    "leL": "K2Node_CallFunction_194", "leR": "K2Node_CallFunction_216",
    "clL": "K2Node_CallFunction_195", "clR": "K2Node_CallFunction_217",
    "selL": "K2Node_CallFunction_197", "selR": "K2Node_CallFunction_233",
    "fmax": "K2Node_CallFunction_251", "dsub": "K2Node_CallFunction_252", "dabs": "K2Node_CallFunction_253",
    "mulK": "K2Node_CallFunction_254", "addF": "K2Node_CallFunction_255",
    "clB": "K2Node_CallFunction_242", "selB": "K2Node_CallFunction_243",
    "getTA": "K2Node_VariableGet_78", "getPrev": "K2Node_VariableGet_79", "fint": "K2Node_CallFunction_246",
}
WNL, WNR = "K2Node_CallFunction_55", "K2Node_CallFunction_91"
M4BR = "K2Node_IfThenElse_4"
UP_N, UP_P = "K2Node_Knot_38", "OutputPin"


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


fn = graph(GF)
entry = next(nid for nid, n in fn.items() if "FunctionEntry" in n["class"])
missing = [k for k, v in MADE.items() if v not in fn]
assert not missing, "함수 노드 미발견: " + json.dumps(missing)
print("[PF] 함수 노드 30종 실재, entry:", entry)

assert APPLY, "apply 인자 필요"

# dt + fint + set 6종 추가
made = dict(MADE)


def add(key, ntype, extra, pos):
    p = {"graph_name": GF, "node_type": ntype, "position": pos}
    p.update(extra)
    r = bq("add_node", p)
    nid = r.get("id") or r.get("node_id")
    made[key] = nid
    print("[ADD]", key, "->", nid)
    return nid


add("dt", "CallFunction", {"function_class": "GameplayStatics", "function_name": "GetWorldDeltaSeconds"}, [2520, 500])
add("fint", "CallFunction", {"function_class": KML, "function_name": "FInterpTo_Constant"}, [2720, 250])
add("setL", "VariableSet", {"variable_name": "LedgeSlopeDzL"}, [1000, -250])
add("setR", "VariableSet", {"variable_name": "LedgeSlopeDzR"}, [1250, -250])
add("setB", "VariableSet", {"variable_name": "LedgeSlopeDzBody"}, [1500, -250])
add("setL0", "VariableSet", {"variable_name": "LedgeSlopeDzL"}, [1000, -80])
add("setR0", "VariableSet", {"variable_name": "LedgeSlopeDzR"}, [1250, -80])
add("setB0", "VariableSet", {"variable_name": "LedgeSlopeDzBody"}, [1500, -80])


def pindef(key, pin, value):
    bq("set_pin_default", {"graph_name": GF, "node_id": made[key], "pin_name": pin, "value": value})


pindef("fcL", "CoordinateSpace", "World")
pindef("fcR", "CoordinateSpace", "World")
pindef("addL", "B", "-8.66")
pindef("addR", "B", "-8.79")
for s in ("L", "R"):
    pindef("le" + s, "B", "45.0")
    pindef("cl" + s, "Min", "-35.0")
    pindef("cl" + s, "Max", "35.0")
    pindef("sel" + s, "B", "0.0")
pindef("mulK", "B", "0.25")
pindef("clB", "Min", "-35.0")
pindef("clB", "Max", "35.0")
pindef("selB", "A", "0.0")
pindef("fint", "InterpSpeed", "45.0")
print("[DEF] 완료")


def wire(sk, sp, tk, tp):
    src = made.get(sk, sk)
    tgt = made.get(tk, tk)
    bq("connect_pins", {"graph_name": GF, "source_node": src, "source_pin": sp,
                        "target_node": tgt, "target_pin": tp})


wire("getSp", "LedgeSplineRef", "isv", "Object")
wire("isv", "ReturnValue", "br", "Condition")
for side, WN in (("L", "WorldNowL"), ("R", "WorldNowR")):
    wire("getSp", "LedgeSplineRef", "fc" + side, "self")
    wire(entry, WN, "fc" + side, "WorldLocation")
    wire("fc" + side, "ReturnValue", "bkC" + side, "InVec")
    wire(entry, WN, "bkW" + side, "InVec")
    wire("bkC" + side, "Z", "add" + side, "A")
    wire("add" + side, "ReturnValue", "sub" + side, "A")
    wire("bkW" + side, "Z", "sub" + side, "B")
    wire("fc" + side, "ReturnValue", "nd" + side, "V1")
    wire(entry, WN, "nd" + side, "V2")
    wire("nd" + side, "ReturnValue", "le" + side, "A")
    wire("sub" + side, "ReturnValue", "cl" + side, "Value")
    wire("cl" + side, "ReturnValue", "sel" + side, "A")
    wire("le" + side, "ReturnValue", "sel" + side, "bPickA")
wire("selL", "ReturnValue", "setL", "LedgeSlopeDzL")
wire("selR", "ReturnValue", "setR", "LedgeSlopeDzR")
wire("selL", "ReturnValue", "fmax", "A")
wire("selR", "ReturnValue", "fmax", "B")
wire("selL", "ReturnValue", "dsub", "A")
wire("selR", "ReturnValue", "dsub", "B")
wire("dsub", "ReturnValue", "dabs", "A")
wire("dabs", "ReturnValue", "mulK", "A")
wire("fmax", "ReturnValue", "addF", "A")
wire("mulK", "ReturnValue", "addF", "B")
wire("addF", "ReturnValue", "clB", "Value")
wire("clB", "ReturnValue", "selB", "B")
wire("getTA", "LedgeTransitActive", "selB", "bPickA")
wire("getPrev", "LedgeSlopeDzBody", "fint", "Current")
wire("selB", "ReturnValue", "fint", "Target")
wire("dt", "ReturnValue", "fint", "DeltaTime")
wire("fint", "ReturnValue", "setB", "LedgeSlopeDzBody")
wire(entry, "then", "br", "execute")
wire("br", "then", "setL", "execute")
wire("setL", "then", "setR", "execute")
wire("setR", "then", "setB", "execute")
wire("br", "else", "setL0", "execute")
wire("setL0", "then", "setR0", "execute")
wire("setR0", "then", "setB0", "execute")
print("[WIRE] 함수 내부 완료")

# ══ 검증: 함수 내부 핵심 링크 ══
fn2 = graph(GF)
ok = True
for tk, tp, sk, sp in ((made["setB"], "LedgeSlopeDzBody", made["fint"], "ReturnValue"),
                       (made["fint"], "DeltaTime", made["dt"], "ReturnValue"),
                       (made["br"], "Condition", made["isv"], "ReturnValue")):
    got = pins(fn2, tk).get(tp, {}).get("connected_to", [])
    good = got == [sk + "." + sp]
    ok = ok and good
    print("[CHK]", "OK " if good else "FAIL", tk + "." + tp, "<-", got)
assert ok

# ══ HandTarget: 호출 스플라이스 ══
r = bq("add_node", {"graph_name": GH, "node_type": "CallFunction",
                    "function_class": "PC_01_ABP_C", "function_name": GF, "position": [4700, -2100]})
callnid = r.get("id") or r.get("node_id")
print("[CALL] +", callnid)
bq("connect_pins", {"graph_name": GH, "source_node": WNL, "source_pin": "ReturnValue",
                    "target_node": callnid, "target_pin": "WorldNowL"})
bq("connect_pins", {"graph_name": GH, "source_node": WNR, "source_pin": "ReturnValue",
                    "target_node": callnid, "target_pin": "WorldNowR"})
bq("disconnect_pins", {"graph_name": GH, "source_node": UP_N, "source_pin": UP_P,
                       "target_node": OLD["br"], "target_pin": "execute"})
bq("connect_pins", {"graph_name": GH, "source_node": UP_N, "source_pin": UP_P,
                    "target_node": callnid, "target_pin": "execute"})
bq("connect_pins", {"graph_name": GH, "source_node": callnid, "source_pin": "then",
                    "target_node": M4BR, "target_pin": "execute"})
print("[CALL] 스플라이스 완료")

# ══ 구 체인 삭제 ══
del_order = ["setL", "setR", "setB", "setL0", "setR0", "setB0", "br",
             "fint", "getPrev", "selB", "getTA", "clB", "addF", "mulK", "dabs", "dsub", "fmax",
             "selL", "selR", "leL", "leR", "ndL", "ndR", "clL", "clR",
             "subL", "subR", "addL", "addR", "bkCL", "bkCR", "bkWL", "bkWR",
             "fcl", "fcr", "isv", "getSp"]
for key in del_order:
    nid = OLD[key]
    cur = graph(GH)
    if nid not in cur:
        print("[DEL] 이미 없음:", key)
        continue
    outs = [c for p in cur[nid]["pins"] if p["direction"] == "output" and not (p.get("is_exec") or p.get("type") == "exec")
            for c in p.get("connected_to", [])]
    if outs:
        print("[DEL] SKIP", key, "데이터 소비자:", outs[:3])
        continue
    bq("remove_node", {"graph_name": GH, "node_id": nid})
    print("[DEL]", key, nid)

r = bq("compile_blueprint", {})
print("[COMPILE]", json.dumps(r)[:300])
