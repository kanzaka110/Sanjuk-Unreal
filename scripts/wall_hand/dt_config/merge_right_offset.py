# -*- coding: utf-8 -*-
"""RightHandHeight(float) → RightHandOffset(Vector2D X=앞뒤, Y=위) 전환.
X = bRight 부호 Select 후 Select_0(속도별 전방) 결과에 가산 → CF_67.B 스플라이스.
Y = 기존 Knot_85 경로 승계. GetConfig remove+재생성(출력 16) + 전 출력 미연결 스캔."""
from mono import bp
import json, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"
PDA = f"{DIR}/PDA_WallHandIKConfig"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
G = "UpdateWallHandIK"
FOLLOW = f"struct:{DIR}/S_WallHandFollow.S_WallHandFollow"

OUTS = [
    ("IKStrengthMax", "float"), ("AttachStartDist", "float"), ("AttachFullDist", "float"),
    ("AttachSpeed", "struct:Vector2D"), ("ReleaseSpeed", "struct:Vector2D"),
    ("TurnReleaseSpeed", "float"), ("FrontHandOffset", "struct:Vector2D"),
    ("RightHandOffset", "struct:Vector2D"), ("SpineLeanMaxDeg", "float"), ("ElbowAngleDeg", "float"),
    ("JogOffset", "struct:Vector2D"), ("RunOffset", "struct:Vector2D"),
    ("SprintOffset", "struct:Vector2D"), ("TurnBlockHold", "float"),
    ("IdleFollow", FOLLOW), ("MoveFollow", FOLLOW),
]

# 유지 출력 재배선 맵 (7/7 FrontHandOffset 통합 후 실측)
REWIRE_OUT = [
    ("IKStrengthMax", "K2Node_Knot_2", "InputPin"),
    ("AttachStartDist", "K2Node_Knot_77", "InputPin"),
    ("AttachFullDist", "K2Node_Knot_79", "InputPin"),
    ("AttachSpeed", "K2Node_CallFunction_102", "InVec"),
    ("ReleaseSpeed", "K2Node_CallFunction_105", "InVec"),
    ("TurnReleaseSpeed", "K2Node_Knot_53", "InputPin"),
    ("FrontHandOffset", "K2Node_CallFunction_96", "InVec"),
    ("SpineLeanMaxDeg", "K2Node_CallFunction_120", "A"),
    ("ElbowAngleDeg", "K2Node_CallFunction_122", "A"),
    ("JogOffset", "K2Node_Knot_55", "InputPin"),
    ("RunOffset", "K2Node_Knot_59", "InputPin"),
    ("SprintOffset", "K2Node_Knot_71", "InputPin"),
    ("TurnBlockHold", "K2Node_Knot_54", "InputPin"),
    ("IdleFollow", "K2Node_BreakStruct_0", "S_WallHandFollow"),
    ("MoveFollow", "K2Node_BreakStruct_1", "S_WallHandFollow"),
]


def run(tag, err, out, n=110):
    print(f"[{tag}]", "ERR" if err else "OK", out[:n])
    if err:
        sys.exit(f"STOP {tag}")
    return out


# ── Phase 1: PDA ──────────────────────────────────────────
run("fn-del", *bp("remove_function", asset_path=PDA, name="GetConfig"))
run("var-del", *bp("remove_variable", asset_path=PDA, name="RightHandHeight"))
run("var-add", *bp("add_variable", asset_path=PDA, name="RightHandOffset",
                   type="struct:Vector2D", default_value="(X=0.0,Y=0.0)"))
run("fn-add", *bp("add_function", asset_path=PDA, name="GetConfig"))
run("fn-outs", *bp("set_function_params", asset_path=PDA, function_name="GetConfig",
                   outputs=[{"name": n, "type": t} for n, t in OUTS]))

out = run("fn-graph", *bp("get_graph_data", asset_path=PDA, graph_name="GetConfig"), 0)
g = json.loads(out)
entry = next(n["id"] for n in g["nodes"] if n["class"] == "K2Node_FunctionEntry")
result = next(n["id"] for n in g["nodes"] if n["class"] == "K2Node_FunctionResult")
run("e→r", *bp("connect_pins", asset_path=PDA, graph_name="GetConfig",
               source_node=entry, source_pin="then", target_node=result, target_pin="execute"))
for i, (n, t) in enumerate(OUTS):
    o = run(f"get-{n}", *bp("add_node", asset_path=PDA, graph_name="GetConfig",
                            node_type="VariableGet", variable_name=n, position=[-400, i * 80]), 60)
    vid = json.loads(o)["id"]
    run(f"wire-{n}", *bp("connect_pins", asset_path=PDA, graph_name="GetConfig",
                         source_node=vid, source_pin=n, target_node=result, target_pin=n), 60)

run("pda-compile", *bp("compile_blueprint", asset_path=PDA), 300)

# ── Phase 2: BP ───────────────────────────────────────────
run("bp-compile1", *bp("compile_blueprint", asset_path=BP), 150)

out = run("bp-graph", *bp("get_graph_data", asset_path=BP, graph_name=G), 0)
g = json.loads(out)
cfg = next(n for n in g["nodes"] if n["class"] == "K2Node_CallFunction"
           and any(p["name"] == "RightHandOffset" for p in n["pins"]))
CFG = cfg["id"]
print(f"== GetConfig 콜노드: {CFG} ==")
existing = {p["name"]: (p.get("connected_to") or []) for p in cfg["pins"]}
sel0 = next(n for n in g["nodes"] if n["id"] == "K2Node_Select_0")
SX, SY = sel0["pos"][0], sel0["pos"][1]


def need(pin, target):
    return not any(target in c for c in existing.get(pin, []))


def con(tag, sn, sp, tn, tp):
    run(tag, *bp("connect_pins", asset_path=BP, graph_name=G,
                 source_node=sn, source_pin=sp, target_node=tn, target_pin=tp), 60)


def add(tag, **kw):
    return json.loads(run(tag, *bp("add_node", asset_path=BP, graph_name=G, **kw), 60))["id"]


if need("execute", "K2Node_FunctionEntry_0"):
    con("exec", "K2Node_FunctionEntry_0", "then", CFG, "execute")
if need("then", "K2Node_VariableSet_0"):
    con("then", CFG, "then", "K2Node_VariableSet_0", "execute")
if need("self", "K2Node_VariableGet_4"):
    con("self", "K2Node_VariableGet_4", "WallHandConfig", CFG, "self")
for sp, tn, tp in REWIRE_OUT:
    if need(sp, tn):
        con(f"rw-{sp}", CFG, sp, tn, tp)

# 신규 체인: RightHandOffset → BreakV2D → (Y→Knot_85) + (X 부호선택→가산→CF_67.B)
BRR = add("brr", node_type="CallFunction", function_name="BreakVector2D",
          position=[cfg["pos"][0] + 250, cfg["pos"][1] + 620])
con("ro→brr", CFG, "RightHandOffset", BRR, "InVec")
con("brr-y", BRR, "Y", "K2Node_Knot_85", "InputPin")

NEG = add("neg", node_type="CallFunction", function_name="Multiply_DoubleDouble",
          position=[SX - 350, SY + 260])
run("neg-b", *bp("set_pin_default", asset_path=BP, graph_name=G, node_id=NEG, pin_name="B", value="-1.0"))
SFX = add("sfx", node_type="CallFunction", function_name="SelectFloat",
          position=[SX - 180, SY + 240])
ADDX = add("addx", node_type="CallFunction", function_name="Add_DoubleDouble",
           position=[SX + 180, SY + 120])
con("x→sfx", BRR, "X", SFX, "A")
con("x→neg", BRR, "X", NEG, "A")
con("neg→sfx", NEG, "ReturnValue", SFX, "B")
con("sign", "K2Node_Knot_15", "OutputPin", SFX, "bPickA")
con("sel→add", "K2Node_Select_0", "ReturnValue", ADDX, "A")
con("sfx→add", SFX, "ReturnValue", ADDX, "B")
con("add→dir", ADDX, "ReturnValue", "K2Node_CallFunction_67", "B")  # 기존 직결 자동 절단

run("bp-compile2", *bp("compile_blueprint", asset_path=BP), 300)

# 최종 스캔: 미연결 출력 (MoveFollow 무음 드랍 함정)
out = run("verify", *bp("get_graph_data", asset_path=BP, graph_name=G), 0)
g = json.loads(out)
cfg = next(n for n in g["nodes"] if n["id"] == CFG)
bad = [p["name"] for p in cfg["pins"] if p["direction"] == "output"
       and p["name"] != "then" and not p.get("connected_to")]
if bad:
    print("!! 미연결 출력:", bad, "— 재연결 시도")
    for sp, tn, tp in REWIRE_OUT:
        if sp in bad:
            con(f"fix-{sp}", CFG, sp, tn, tp)
    if "RightHandOffset" in bad:
        con("fix-ro", CFG, "RightHandOffset", BRR, "InVec")
    run("bp-compile3", *bp("compile_blueprint", asset_path=BP), 300)
else:
    print("미연결 출력: 없음")
print("== merge_right done ==")
