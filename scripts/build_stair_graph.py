"""UpdateStairAlpha 함수 내부 그래프 자동 구축.

노드 → 연결 순서:
  Entry → Sub(DeltaZ) → Abs → Divide(VelSpeed) → Greater → Branch
    True  → Set Timer = RecoveryTime
    False → Sub(Timer-Dt) → Max(0) → Set Timer
  → Divide(Ratio) → Lerp(1.0, Min, Ratio) → FInterpTo → Set FootPlacementAlpha
  → Set LastCapsuleZ
"""
import json
import subprocess

MCP = "http://localhost:9316/mcp"
BP = "/Game/ART/Character/PC/PC_01/Blueprint/PC_01_ABP"
FN = "UpdateStairAlpha"


def call(action: str, args: dict) -> dict:
    payload = {
        "jsonrpc": "2.0", "method": "tools/call", "id": 1,
        "params": {"name": "blueprint_query",
                   "arguments": {"action": action, **args}}
    }
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", MCP,
         "-H", "Content-Type: application/json",
         "-d", json.dumps(payload)],
        capture_output=True, text=True, timeout=30)
    d = json.loads(r.stdout)
    txt = d.get("result", {}).get("content", [{}])[0].get("text", "")
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return {"_raw": txt}


def add_variable_get(name: str, x: int, y: int) -> str:
    res = call("add_node", {
        "asset_path": BP, "graph_name": FN,
        "node_type": "VariableGet",
        "variable_name": name,
        "position": {"x": x, "y": y},
    })
    nid = res.get("id")
    print(f"  [VarGet] {name} → {nid}")
    return nid


def add_variable_set(name: str, x: int, y: int) -> str:
    res = call("add_node", {
        "asset_path": BP, "graph_name": FN,
        "node_type": "VariableSet",
        "variable_name": name,
        "position": {"x": x, "y": y},
    })
    nid = res.get("id")
    print(f"  [VarSet] {name} → {nid}")
    return nid


def add_call(function_name: str, class_path: str, x: int, y: int, alias: str = "") -> str:
    res = call("add_node", {
        "asset_path": BP, "graph_name": FN,
        "node_type": "CallFunction",
        "function_name": function_name,
        "function_class": class_path,
        "position": {"x": x, "y": y},
    })
    nid = res.get("id")
    print(f"  [Call] {alias or function_name} → {nid}")
    return nid


def add_branch(x: int, y: int) -> str:
    res = call("add_node", {
        "asset_path": BP, "graph_name": FN,
        "node_type": "Branch",
        "position": {"x": x, "y": y},
    })
    nid = res.get("id")
    print(f"  [Branch] → {nid}")
    return nid


def connect(src_node: str, src_pin: str, dst_node: str, dst_pin: str) -> None:
    res = call("connect_pins", {
        "asset_path": BP, "graph_name": FN,
        "source_node": src_node, "source_pin": src_pin,
        "target_node": dst_node, "target_pin": dst_pin,
    })
    ok = res.get("success", False)
    mark = "[OK]" if ok else "[FAIL]"
    print(f"  {mark} {src_node}.{src_pin} -> {dst_node}.{dst_pin}"
          + ("" if ok else f" | {res}"))


def set_default(node: str, pin: str, value: str) -> None:
    res = call("set_pin_default", {
        "asset_path": BP, "graph_name": FN,
        "node_id": node, "pin_name": pin, "value": value,
    })
    ok = res.get("success", False)
    mark = "[OK]" if ok else "[FAIL]"
    print(f"  {mark} set {node}.{pin} = {value}"
          + ("" if ok else f" | {res}"))


# ============================================================
# 1. 현재 그래프의 Entry 노드 ID 확인
# ============================================================
print("=== Entry 노드 확인 ===")
res = call("get_graph_data", {"asset_path": BP, "graph_name": FN})
entry_id = None
for n in res.get("nodes", []):
    if n.get("class") == "K2Node_FunctionEntry":
        entry_id = n.get("id")
        break
print(f"  Entry = {entry_id}")
if not entry_id:
    print("  [ERR] Entry not found")
    raise SystemExit

# ============================================================
# 2. 노드 생성 (변수 Get/Set + Math 연산)
# ============================================================
print("\n=== 노드 생성 ===")

KML = "/Script/Engine.KismetMathLibrary"

# --- 변수 Get ---
get_last_z   = add_variable_get("LastCapsuleZ",          -800,  100)
get_thresh   = add_variable_get("StairVerticalSpeedThreshold", -400, -200)
get_rec_time_1 = add_variable_get("StairAlphaRecoveryTime",     0, -200)
get_timer_fb = add_variable_get("StairAlphaRecoveryTimer",   -100,  500)
get_timer_2  = add_variable_get("StairAlphaRecoveryTimer",    400,  100)
get_rec_time_2 = add_variable_get("StairAlphaRecoveryTime",   400,  200)
get_min      = add_variable_get("StairAlphaMin",              800,  100)
get_fp_alpha = add_variable_get("FootPlacementAlpha",        1200,  100)

# --- Math calls ---
sub_dz    = add_call("Subtract_DoubleDouble", KML, -500, 100, "Sub DeltaZ")
abs_dz    = add_call("Abs",                    KML, -350, 100, "Abs")
div_vs    = add_call("Divide_DoubleDouble",    KML, -200, 100, "Div VertSpeed")
greater   = add_call("Greater_DoubleDouble",   KML,  -50, 100, "Greater")

sub_timer = add_call("Subtract_DoubleDouble", KML,  150, 500, "Sub Timer")
max_timer = add_call("Max",                    KML,  300, 500, "Max(0, ...)")

div_ratio = add_call("Divide_DoubleDouble",    KML,  550, 150, "Div Ratio")
lerp_alpha = add_call("Lerp",                  KML,  900, 100, "Lerp")
finterp   = add_call("FInterpTo",              KML, 1300, 150, "FInterpTo")

# --- Branch ---
branch = add_branch(100, 100)

# --- Variable Set ---
set_timer_t = add_variable_set("StairAlphaRecoveryTimer", 200, 0,  )
set_timer_f = add_variable_set("StairAlphaRecoveryTimer", 400, 500)
set_fp      = add_variable_set("FootPlacementAlpha",     1550, 150)
set_last_z  = add_variable_set("LastCapsuleZ",           1800, 150)

# ============================================================
# 3. 연결 (데이터 흐름 먼저, exec는 나중)
# ============================================================
print("\n=== 데이터 연결 ===")

# VerticalSpeed 계산 체인
connect(entry_id,   "CurrentCapsuleZ",  sub_dz,    "A")
connect(get_last_z, "LastCapsuleZ",     sub_dz,    "B")
connect(sub_dz,     "ReturnValue",      abs_dz,    "A")
connect(abs_dz,     "ReturnValue",      div_vs,    "A")
connect(entry_id,   "DeltaTime",        div_vs,    "B")
connect(div_vs,     "ReturnValue",      greater,   "A")
connect(get_thresh, "StairVerticalSpeedThreshold", greater, "B")

# Branch condition
connect(greater,    "ReturnValue",      branch,    "Condition")

# True: Timer = RecoveryTime
connect(get_rec_time_1, "StairAlphaRecoveryTime", set_timer_t, "StairAlphaRecoveryTimer")

# False: Timer = max(0, Timer - DeltaTime)
connect(get_timer_fb,"StairAlphaRecoveryTimer",   sub_timer, "A")
connect(entry_id,    "DeltaTime",                 sub_timer, "B")
connect(sub_timer,   "ReturnValue",               max_timer, "A")
# Max B = 0 default
connect(max_timer,   "ReturnValue",               set_timer_f, "StairAlphaRecoveryTimer")

# TargetAlpha = Lerp(1.0, Min, Ratio) — Ratio = Timer / RecoveryTime
connect(get_timer_2,   "StairAlphaRecoveryTimer",  div_ratio, "A")
connect(get_rec_time_2,"StairAlphaRecoveryTime",   div_ratio, "B")
# Lerp A = 1.0 (default), B = Min, Alpha = Ratio
connect(get_min,       "StairAlphaMin",            lerp_alpha, "B")
connect(div_ratio,     "ReturnValue",              lerp_alpha, "Alpha")

# FInterpTo(Current=FootPlacementAlpha, Target=Lerp결과, DeltaTime, Speed=15)
connect(get_fp_alpha, "FootPlacementAlpha",         finterp, "Current")
connect(lerp_alpha,   "ReturnValue",                finterp, "Target")
connect(entry_id,     "DeltaTime",                  finterp, "DeltaTime")

# Set FootPlacementAlpha
connect(finterp,      "ReturnValue",                set_fp, "FootPlacementAlpha")

# Set LastCapsuleZ
connect(entry_id,     "CurrentCapsuleZ",            set_last_z, "LastCapsuleZ")

# ============================================================
# 4. exec 체인
# ============================================================
print("\n=== exec 체인 ===")
connect(entry_id,    "then",      branch,      "execute")
connect(branch,      "then",      set_timer_t, "execute")   # True
connect(branch,      "else",      set_timer_f, "execute")   # False
connect(set_timer_t, "then",      set_fp,      "execute")
connect(set_timer_f, "then",      set_fp,      "execute")
connect(set_fp,      "then",      set_last_z,  "execute")

# ============================================================
# 5. 핀 default
# ============================================================
print("\n=== 핀 default ===")
set_default(max_timer, "B", "0.0")
set_default(lerp_alpha, "A", "1.0")
set_default(finterp, "InterpSpeed", "15.0")

# ============================================================
# 6. 컴파일
# ============================================================
print("\n=== 컴파일 ===")
res = call("compile_blueprint", {"asset_path": BP})
print(f"  {res}")
