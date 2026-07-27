# 손별 창 상대 램프 (2026-07-25) — 경사 이동 스윙 방향 유도
# 설계: 각 손의 릴리즈 창(L 0.10~0.45 / R 0.50~0.85) 내 상대 진행도 t를
#   LedgeProcRampL/R = (창 안이면) FClamp((p-w0)/(w1-w0),0,1) × LedgeProcRampGain, (밖이면) 0
#   으로 계산 → Ledge_HandAlpha FMax B(구 LedgeSlopeMoveFloor 스칼라)를 손별 램프로 교체.
# 창 시작=릴리즈 직후 유도 0(자유 스윙) → 창 끝=플랜트 시점 유도 최대(라인 위 타깃 견인).
# 실행: py ramp_build.py         (사전 점검만)
#       py ramp_build.py apply   (적용)
import json
import sys
import urllib.request

URL = "http://localhost:9316/mcp"
ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GF = "Ledge_ProcWindow"
GA = "Ledge_HandAlpha"
KML = "KismetMathLibrary"
WIN = {"L": ("0.10", "0.45"), "R": ("0.50", "0.85")}
SPAN = {"L": "0.35", "R": "0.35"}
APPLY = len(sys.argv) > 1 and sys.argv[1] == "apply"

# ProcWindow 기존 노드 (ramp_probe.py 2026-07-25 실측)
PROG = "K2Node_CallFunction_20"        # FClamp(prog 0..1)
INWIN = {"L": "K2Node_CallFunction_23", "R": "K2Node_CallFunction_27"}  # BooleanAND 창 판정
SET_WIN = {"then_tail": "K2Node_VariableSet_1", "else_tail": "K2Node_VariableSet_3"}
# HandAlpha 기존 노드
FMAX = {"L": "K2Node_CallFunction_4", "R": "K2Node_CallFunction_5"}
GET_FLOOR = "K2Node_VariableGet_4"     # LedgeSlopeMoveFloor getter (양손 FMax B)


def call(tool: str, action: str, params: dict, timeout: int = 300) -> dict:
    body = {"jsonrpc": "2.0", "method": "tools/call", "id": 1,
            "params": {"name": tool, "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    res = r["result"]
    txt = res["content"][0]["text"]
    if res.get("isError"):
        raise RuntimeError(action + ": " + txt[:400])
    return json.loads(txt)


def bq(action: str, params: dict) -> dict:
    p = {"asset_path": ABP}
    p.update(params)
    return call("blueprint_query", action, p)


def graph(g: str) -> dict:
    return {n["id"]: n for n in bq("get_graph_data", {"graph_name": g})["nodes"]}


def pins(nodes: dict, nid: str) -> dict:
    return {p["name"]: p for p in nodes[nid].get("pins", [])}


def pie_on() -> bool:
    r = call("editor_query", "run_python", {
        "command": "import unreal;print(unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None)",
        "mode": "execute_file"})
    return "True" in json.dumps(r.get("output", []))


# ── 사전 점검 ──
pw = graph(GF)
ha = graph(GA)
checks = [
    (PROG in pw, f"prog 노드 {PROG}"),
    (all(n in pw for n in INWIN.values()), "창 판정 AND 노드"),
    (all(n in pw for n in SET_WIN.values()), "Set 꼬리 노드"),
    (all(n in ha for n in FMAX.values()), "HandAlpha FMax 노드"),
]
fmax_b_ok = all(
    pins(ha, FMAX[s])["B"]["connected_to"] == [GET_FLOOR + ".LedgeSlopeMoveFloor"]
    for s in ("L", "R"))
checks.append((fmax_b_ok, "FMax B ← LedgeSlopeMoveFloor 스칼라 (교체 전 상태)"))
then_tail_free = not pins(pw, SET_WIN["then_tail"]).get("then", {}).get("connected_to")
else_tail_free = not pins(pw, SET_WIN["else_tail"]).get("then", {}).get("connected_to")
checks.append((then_tail_free, "then 꼬리 VariableSet_1.then 비어있음"))
checks.append((else_tail_free, "else 꼬리 VariableSet_3.then 비어있음"))
ok = True
for good, label in checks:
    print("[PF]", "OK " if good else "FAIL", label)
    ok = ok and good
if not APPLY:
    print("[PF] 사전 점검", "통과 — apply로 실행" if ok else "실패")
    sys.exit(0 if ok else 1)
assert ok, "사전 점검 실패 — 그래프 상태가 예상과 다름"
assert not pie_on(), "PIE 실행 중 — 종료 후 재실행"

# ── 1) 변수 ──
existing = {v["name"] for v in bq("get_variables", {}).get("variables", [])}
for v in ("LedgeProcRampL", "LedgeProcRampR", "LedgeProcRampGain"):
    if v not in existing:
        bq("add_variable", {"name": v, "type": "float", "category": "Ledge|ProcWin"})
        print("[VAR] +", v)
try:
    bq("set_variable_defaults", {"name": "LedgeProcRampGain", "default_value": "1.0"})
    print("[VAR] Gain default 1.0 set")
except RuntimeError as e:
    print("[VAR] Gain default 실패 — 수동 설정 필요:", str(e)[:120])

# ── 2) Ledge_ProcWindow 램프 체인 ──
made = {}


def add(key: str, ntype: str, extra: dict, pos: list) -> str:
    p = {"graph_name": GF, "node_type": ntype, "position": pos}
    p.update(extra)
    r = bq("add_node", p)
    nid = r.get("id") or r.get("node_id")
    made[key] = nid
    return nid


def wire(sk: str, sp: str, tk: str, tp: str) -> None:
    bq("connect_pins", {"graph_name": GF,
                        "source_node": made.get(sk, sk), "source_pin": sp,
                        "target_node": made.get(tk, tk), "target_pin": tp})


def pindef(key: str, pin: str, value: str) -> None:
    bq("set_pin_default", {"graph_name": GF, "node_id": made[key], "pin_name": pin, "value": value})


X, Y = 2400, 900
add("gGain", "VariableGet", {"variable_name": "LedgeProcRampGain"}, [X, Y + 260])
for i, s in enumerate(("L", "R")):
    yo = Y + i * 340
    add("sub" + s, "CallFunction", {"function_class": KML, "function_name": "Subtract_DoubleDouble"}, [X, yo])
    add("div" + s, "CallFunction", {"function_class": KML, "function_name": "Divide_DoubleDouble"}, [X + 160, yo])
    add("clp" + s, "CallFunction", {"function_class": KML, "function_name": "FClamp"}, [X + 320, yo])
    add("mul" + s, "CallFunction", {"function_class": KML, "function_name": "Multiply_DoubleDouble"}, [X + 480, yo])
    add("sel" + s, "CallFunction", {"function_class": KML, "function_name": "SelectFloat"}, [X + 640, yo])
    pindef("sub" + s, "B", WIN[s][0])
    pindef("div" + s, "B", SPAN[s])
    pindef("clp" + s, "Min", "0.0")
    pindef("clp" + s, "Max", "1.0")
    pindef("sel" + s, "B", "0.0")
    wire(PROG, "ReturnValue", "sub" + s, "A")
    wire("sub" + s, "ReturnValue", "div" + s, "A")
    wire("div" + s, "ReturnValue", "clp" + s, "Value")
    wire("clp" + s, "ReturnValue", "mul" + s, "A")
    wire("gGain", "LedgeProcRampGain", "mul" + s, "B")
    wire("mul" + s, "ReturnValue", "sel" + s, "A")
    wire(INWIN[s], "ReturnValue", "sel" + s, "bPickA")

# then 경로: WinR Set 뒤에 램프 Set 2개
add("setRampL", "VariableSet", {"variable_name": "LedgeProcRampL"}, [X + 840, Y])
add("setRampR", "VariableSet", {"variable_name": "LedgeProcRampR"}, [X + 1040, Y])
wire("selL", "ReturnValue", "setRampL", "LedgeProcRampL")
wire("selR", "ReturnValue", "setRampR", "LedgeProcRampR")
wire(SET_WIN["then_tail"], "then", "setRampL", "execute")
wire("setRampL", "then", "setRampR", "execute")
# else 경로: Win 1.0 Set 뒤에 램프 0 Set 2개
add("setRampL0", "VariableSet", {"variable_name": "LedgeProcRampL"}, [X + 840, Y + 500])
add("setRampR0", "VariableSet", {"variable_name": "LedgeProcRampR"}, [X + 1040, Y + 500])
bq("set_pin_default", {"graph_name": GF, "node_id": made["setRampL0"], "pin_name": "LedgeProcRampL", "value": "0.0"})
bq("set_pin_default", {"graph_name": GF, "node_id": made["setRampR0"], "pin_name": "LedgeProcRampR", "value": "0.0"})
wire(SET_WIN["else_tail"], "then", "setRampL0", "execute")
wire("setRampL0", "then", "setRampR0", "execute")
print("[PW] 램프 체인 배선 완료")

# ── 3) HandAlpha FMax B 재배선 ──
for s in ("L", "R"):
    r = bq("add_node", {"graph_name": GA, "node_type": "VariableGet",
                        "variable_name": "LedgeProcRamp" + s,
                        "position": [1000, 380 if s == "L" else 560]})
    gv = r.get("id") or r.get("node_id")
    bq("disconnect_pins", {"graph_name": GA, "source_node": GET_FLOOR,
                           "source_pin": "LedgeSlopeMoveFloor",
                           "target_node": FMAX[s], "target_pin": "B"})
    bq("connect_pins", {"graph_name": GA, "source_node": gv,
                        "source_pin": "LedgeProcRamp" + s,
                        "target_node": FMAX[s], "target_pin": "B"})
    made["haGet" + s] = gv
    print("[HA] FMax", s, "B ← LedgeProcRamp" + s)

# ── 4) 컴파일 + 링크 검증 ──
r = bq("compile_blueprint", {})
print("[COMPILE]", json.dumps(r)[:200])

pw2 = graph(GF)
ha2 = graph(GA)
v = []
v.append((pins(pw2, made["setRampL"])["LedgeProcRampL"]["connected_to"] == [made["selL"] + ".ReturnValue"], "PW SetRampL ← selL"))
v.append((pins(pw2, made["setRampR"])["LedgeProcRampR"]["connected_to"] == [made["selR"] + ".ReturnValue"], "PW SetRampR ← selR"))
v.append((pins(pw2, made["setRampL"])["execute"]["connected_to"] == [SET_WIN["then_tail"] + ".then"], "PW then 꼬리 → SetRampL"))
v.append((pins(pw2, made["setRampL0"])["execute"]["connected_to"] == [SET_WIN["else_tail"] + ".then"], "PW else 꼬리 → SetRampL0"))
for s in ("L", "R"):
    v.append((pins(ha2, FMAX[s])["B"]["connected_to"] == [made["haGet" + s] + ".LedgeProcRamp" + s], f"HA FMax {s} B ← Ramp{s}"))
    v.append((pins(pw2, made["sel" + s])["bPickA"]["connected_to"] == [INWIN[s] + ".ReturnValue"], f"PW sel{s} 게이트"))
    v.append((pins(pw2, made["sub" + s])["A"]["connected_to"] == [PROG + ".ReturnValue"], f"PW sub{s} ← prog"))
allok = True
for good, label in v:
    print("[CHK]", "OK " if good else "FAIL", label)
    allok = allok and good
gain = next((x for x in bq("get_variables", {}).get("variables", []) if x["name"] == "LedgeProcRampGain"), {})
print("[VAR] Gain =", json.dumps(gain))
assert allok, "링크 검증 실패"
print("[DONE] 컴파일+검증 통과 — PIE 실측 대기")
