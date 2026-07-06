# -*- coding: utf-8 -*-
"""Step6: PDA_WallHandIKConfig에 GetConfig 함수 (출력 16) + FrontAttachCurve CDO 보정."""
from mono import bp
import json, sys

DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"
PDA = f"{DIR}/PDA_WallHandIKConfig"
G = "GetConfig"

VARS = [
    ("IKStrengthMax", "float"), ("AttachStartDist", "float"), ("AttachFullDist", "float"),
    ("FrontFullDist", "float"), ("AttachCurve", "object:CurveFloat"), ("FrontAttachCurve", "object:CurveFloat"),
    ("AttachDuration", "float"), ("ReleaseDuration", "float"), ("TurnReleaseDuration", "float"),
    ("FrontHandHalfWidth", "float"), ("FrontHandHeight", "float"), ("RightHandHeight", "float"),
    ("JogOffset", "struct:Vector2D"), ("RunOffset", "struct:Vector2D"), ("SprintOffset", "struct:Vector2D"),
    ("TurnBlockHold", "float"),
]

def run(tag, err, out, n=130):
    print(f"[{tag}]", "ERR" if err else "OK", out[:n])
    if err:
        sys.exit(f"STOP {tag}")
    return out

# CDO 커브 참조 보정 (커브보다 변수 먼저 만들어서 None일 수 있음)
run("cdo-front", *bp("set_cdo_property", asset_path=PDA, property_name="FrontAttachCurve",
                     value=f"{DIR}/C_WallHandFrontAttach.C_WallHandFrontAttach"))
run("cdo-attach", *bp("set_cdo_property", asset_path=PDA, property_name="AttachCurve",
                      value=f"{DIR}/C_WallHandAttach.C_WallHandAttach"))

run("fn", *bp("add_function", asset_path=PDA, function_name=G))
run("outs", *bp("set_function_params", asset_path=PDA, function_name=G,
                outputs=[{"name": n, "type": t} for n, t in VARS]))

# 결과 노드 ID 확보
out = run("graph", *bp("get_graph_data", asset_path=PDA, graph_name=G), 0)
g = json.loads(out)
entry = next(n["id"] for n in g["nodes"] if n["class"] == "K2Node_FunctionEntry")
result = next(n["id"] for n in g["nodes"] if n["class"] == "K2Node_FunctionResult")
run("e→r", *bp("connect_pins", asset_path=PDA, graph_name=G,
               source_node=entry, source_pin="then", target_node=result, target_pin="execute"))

for i, (n, t) in enumerate(VARS):
    out = run(f"get-{n}", *bp("add_node", asset_path=PDA, graph_name=G,
                              node_type="VariableGet", variable_name=n,
                              position=[-400, i * 80]))
    vid = json.loads(out)["id"]
    run(f"wire-{n}", *bp("connect_pins", asset_path=PDA, graph_name=G,
                         source_node=vid, source_pin=n, target_node=result, target_pin=n))

run("compile", *bp("compile_blueprint", asset_path=PDA), 300)
run("save", *bp("save_asset", asset_path=PDA), 120)
print("== step6 done ==")
