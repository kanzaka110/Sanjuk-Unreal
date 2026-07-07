# -*- coding: utf-8 -*-
"""벽별 설정 분리 Script A: UDS S_WallHandSideConfig/S_WallHandFrontConfig 생성
+ PDA 재구조 (구 8필드 제거 → RWall/LWall/FWall, 최종 11필드) + GetConfig 재생성(출력 11)."""
from mono import bp
import json, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"
PDA = f"{DIR}/PDA_WallHandIKConfig"
SIDE = f"{DIR}/S_WallHandSideConfig"
FRONT = f"{DIR}/S_WallHandFrontConfig"
FOLLOW = f"struct:{DIR}/S_WallHandFollow.S_WallHandFollow"

SIDE_FIELDS = [
    {"name": "IKStrength", "type": "float", "default_value": "1.0"},
    {"name": "AttachStartDist", "type": "float", "default_value": "60.0"},
    {"name": "AttachFullDist", "type": "float", "default_value": "45.0"},
    {"name": "HandOffset", "type": "struct:Vector2D", "default_value": "(X=0.0,Y=0.0)"},
    {"name": "JogOffset", "type": "struct:Vector2D", "default_value": "(X=5.0,Y=0.0)"},
    {"name": "RunOffset", "type": "struct:Vector2D", "default_value": "(X=20.0,Y=-5.0)"},
    {"name": "SprintOffset", "type": "struct:Vector2D", "default_value": "(X=60.0,Y=-10.0)"},
]
FRONT_FIELDS = [
    {"name": "IKStrength", "type": "float", "default_value": "1.0"},
    {"name": "AttachStartDist", "type": "float", "default_value": "60.0"},
    {"name": "AttachFullDist", "type": "float", "default_value": "45.0"},
    {"name": "HandOffset", "type": "struct:Vector2D", "default_value": "(X=12.4,Y=12.4)"},
]

OUTS = [
    ("RWall", f"struct:{SIDE}.S_WallHandSideConfig"),
    ("LWall", f"struct:{SIDE}.S_WallHandSideConfig"),
    ("FWall", f"struct:{FRONT}.S_WallHandFrontConfig"),
    ("AttachSpeed", "struct:Vector2D"), ("ReleaseSpeed", "struct:Vector2D"),
    ("TurnReleaseSpeed", "float"), ("SpineLeanMaxDeg", "float"), ("ElbowAngleDeg", "float"),
    ("TurnBlockHold", "float"), ("IdleFollow", FOLLOW), ("MoveFollow", FOLLOW),
]

REMOVE_VARS = ["IKStrengthMax", "AttachStartDist", "AttachFullDist", "FrontHandOffset",
               "RightHandOffset", "JogOffset", "RunOffset", "SprintOffset"]


def run(tag, err, out, n=120):
    print(f"[{tag}]", "ERR" if err else "OK", out[:n])
    if err:
        sys.exit(f"STOP {tag}")
    return out


# 1) UDS 2종
for path, fields in ((SIDE, SIDE_FIELDS), (FRONT, FRONT_FIELDS)):
    err, out = bp("create_user_defined_struct", save_path=path, fields=fields)
    if err and "exist" in out.lower():
        print(f"[uds {path.split('/')[-1]}] SKIP(존재)")
    else:
        run(f"uds {path.split('/')[-1]}", err, out)

# 2) PDA 재구조
run("fn-del", *bp("remove_function", asset_path=PDA, name="GetConfig"))
for v in REMOVE_VARS:
    run(f"del-{v}", *bp("remove_variable", asset_path=PDA, name=v), 60)
run("add-RWall", *bp("add_variable", asset_path=PDA, name="RWall",
                     type=f"struct:{SIDE}.S_WallHandSideConfig"))
run("add-LWall", *bp("add_variable", asset_path=PDA, name="LWall",
                     type=f"struct:{SIDE}.S_WallHandSideConfig"))
run("add-FWall", *bp("add_variable", asset_path=PDA, name="FWall",
                     type=f"struct:{FRONT}.S_WallHandFrontConfig"))

# 3) GetConfig 재생성 (출력 11)
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
                            node_type="VariableGet", variable_name=n, position=[-400, i * 80]), 50)
    vid = json.loads(o)["id"]
    run(f"wire-{n}", *bp("connect_pins", asset_path=PDA, graph_name="GetConfig",
                         source_node=vid, source_pin=n, target_node=result, target_pin=n), 50)

run("pda-compile", *bp("compile_blueprint", asset_path=PDA), 300)
run("pda-save", *bp("save_asset", asset_path=PDA), 100)
print("== Script A done ==")
