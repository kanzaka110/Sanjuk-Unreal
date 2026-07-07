# -*- coding: utf-8 -*-
"""FrontHandHalfWidth + FrontHandHeight → FrontHandOffset(Vector2D X=폭, Y=높이) 통합.
PDA 17→16필드. GetConfig remove+재생성(출력 16) → BP CF_55 재배선(무음 드랍 대비 전량)."""
from mono import bp
import json, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"
PDA = f"{DIR}/PDA_WallHandIKConfig"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
G = "UpdateWallHandIK"
FOLLOW = f"struct:{DIR}/S_WallHandFollow.S_WallHandFollow"

# GetConfig 출력 16 (현행 콜노드 핀 순서 유지, HalfWidth/Height 자리에 Offset)
OUTS = [
    ("IKStrengthMax", "float"), ("AttachStartDist", "float"), ("AttachFullDist", "float"),
    ("AttachSpeed", "struct:Vector2D"), ("ReleaseSpeed", "struct:Vector2D"),
    ("TurnReleaseSpeed", "float"), ("FrontHandOffset", "struct:Vector2D"),
    ("RightHandHeight", "float"), ("SpineLeanMaxDeg", "float"), ("ElbowAngleDeg", "float"),
    ("JogOffset", "struct:Vector2D"), ("RunOffset", "struct:Vector2D"),
    ("SprintOffset", "struct:Vector2D"), ("TurnBlockHold", "float"),
    ("IdleFollow", FOLLOW), ("MoveFollow", FOLLOW),
]

# BP 콜사이트 재배선 맵 (실측 덤프 기준). (src_pin, target_node, target_pin)
REWIRE_OUT = [
    ("IKStrengthMax", "K2Node_Knot_2", "InputPin"),
    ("AttachStartDist", "K2Node_Knot_77", "InputPin"),
    ("AttachFullDist", "K2Node_Knot_79", "InputPin"),
    ("AttachSpeed", "K2Node_CallFunction_102", "InVec"),
    ("ReleaseSpeed", "K2Node_CallFunction_105", "InVec"),
    ("TurnReleaseSpeed", "K2Node_Knot_53", "InputPin"),
    ("RightHandHeight", "K2Node_Knot_85", "InputPin"),
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


def soft(tag, err, out, n=110):
    print(f"[{tag}]", "ERR" if err else "OK", out[:n])
    return err


# ── Phase 1: PDA ──────────────────────────────────────────
run("fn-del", *bp("remove_function", asset_path=PDA, name="GetConfig"))
run("var-del-w", *bp("remove_variable", asset_path=PDA, name="FrontHandHalfWidth"))
run("var-del-h", *bp("remove_variable", asset_path=PDA, name="FrontHandHeight"))
run("var-add", *bp("add_variable", asset_path=PDA, name="FrontHandOffset",
                   type="struct:Vector2D", default_value="(X=12.4,Y=12.4)"))
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

# ── Phase 2: BP 리컴파일(콜노드 재구성) + 전량 재배선 ──────
run("bp-compile1", *bp("compile_blueprint", asset_path=BP), 200)

out = run("bp-graph", *bp("get_graph_data", asset_path=BP, graph_name=G), 0)
g = json.loads(out)
cfg = next(n for n in g["nodes"] if n["class"] == "K2Node_CallFunction"
           and any(p["name"] == "FrontHandOffset" for p in n["pins"]))
CFG = cfg["id"]
print(f"== GetConfig 콜노드: {CFG} ==")
existing = {p["name"]: (p.get("connected_to") or []) for p in cfg["pins"]}


def need(pin, target):
    return not any(target in c for c in existing.get(pin, []))


def con(tag, sn, sp, tn, tp):
    run(tag, *bp("connect_pins", asset_path=BP, graph_name=G,
                 source_node=sn, source_pin=sp, target_node=tn, target_pin=tp), 60)


# exec/self
if need("execute", "K2Node_FunctionEntry_0"):
    con("exec", "K2Node_FunctionEntry_0", "then", CFG, "execute")
if need("then", "K2Node_VariableSet_0"):
    con("then", CFG, "then", "K2Node_VariableSet_0", "execute")
if need("self", "K2Node_VariableGet_4"):
    con("self", "K2Node_VariableGet_4", "WallHandConfig", CFG, "self")
# 유지 출력 15
for sp, tn, tp in REWIRE_OUT:
    if need(sp, tn):
        con(f"rw-{sp}", CFG, sp, tn, tp)
# 신규: FrontHandOffset → BreakVector2D → 기존 Knot 4개
o = run("brf", *bp("add_node", asset_path=BP, graph_name=G, node_type="CallFunction",
                   function_name="BreakVector2D", position=[cfg["pos"][0] + 250, cfg["pos"][1] + 500]), 60)
BRF = json.loads(o)["id"]
con("fo→brf", CFG, "FrontHandOffset", BRF, "InVec")
con("brf-x1", BRF, "X", "K2Node_Knot_92", "InputPin")
con("brf-x2", BRF, "X", "K2Node_Knot_93", "InputPin")
con("brf-y1", BRF, "Y", "K2Node_Knot_74", "InputPin")
con("brf-y2", BRF, "Y", "K2Node_Knot_90", "InputPin")

run("bp-compile2", *bp("compile_blueprint", asset_path=BP), 300)
print("== merge done — 검증 덤프는 별도 ==")
