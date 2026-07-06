# -*- coding: utf-8 -*-
"""v2 ABP: 변수 7종(기본값=현행 fail-safe) + SetWallHandConfig 싱크 + 핀→변수 교체.
동작 로직 무변경 — FInterpTo 체계 유지, 상수만 변수화."""
from mono import bp
import json, sys

ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"

def run(tag, err, out, n=100):
    print(f"[{tag}]", "ERR" if err else "OK", out[:n])
    if err:
        sys.exit(f"STOP {tag}")
    return out

VARS = [("WHIKStrength", "1.0"), ("WHAttachSpdStart", "3.0"), ("WHAttachSpdEnd", "12.0"),
        ("WHRelSpdSlow", "4.5"), ("WHRelSpdFast", "8.0"), ("WHTurnRelSpd", "28.0"),
        ("WHTurnBlockHold", "0.8")]
for n, d in VARS:
    run(f"var {n}", *bp("add_variable", asset_path=ABP, name=n, type="float",
                        default_value=d, category="WallHandIK"))

# 싱크 함수
GB = "SetWallHandConfig"
run("fn", *bp("add_function", asset_path=ABP, function_name=GB))
run("ins", *bp("set_function_params", asset_path=ABP, function_name=GB,
               inputs=[{"name": "In" + n, "type": "float"} for n, d in VARS]))
ids = {}
for i, (n, d) in enumerate(VARS):
    out = run(f"set {n}", *bp("add_node", asset_path=ABP, graph_name=GB,
                              node_type="VariableSet", variable_name=n,
                              position=[300 + i * 220, 0]), 60)
    ids[n] = json.loads(out)["id"]
out = run("g", *bp("get_graph_data", asset_path=ABP, graph_name=GB), 0)
g = json.loads(out)
entry = next(nd["id"] for nd in g["nodes"] if nd["class"] == "K2Node_FunctionEntry")
prev = entry
for n, d in VARS:
    run(f"x {n}", *bp("connect_pins", asset_path=ABP, graph_name=GB,
                      source_node=prev, source_pin="then",
                      target_node=ids[n], target_pin="execute"), 60)
    run(f"d {n}", *bp("connect_pins", asset_path=ABP, graph_name=GB,
                      source_node=entry, source_pin="In" + n,
                      target_node=ids[n], target_pin=n), 60)
    prev = ids[n]

# alpha 함수: 속도맵/턴 핀 → 변수
GA = "SetSmoothedWallHandAlpha"
def vg(graph, var, pos):
    out = run(f"vg {var}", *bp("add_node", asset_path=ABP, graph_name=graph,
                               node_type="VariableGet", variable_name=var, position=pos), 60)
    return json.loads(out)["id"]

for var, tn, tp, pos in [
    ("WHAttachSpdStart", "K2Node_CallFunction_16", "OutRangeA", [-700, 350]),
    ("WHAttachSpdEnd",   "K2Node_CallFunction_16", "OutRangeB", [-700, 430]),
    ("WHRelSpdSlow",     "K2Node_CallFunction_6",  "OutRangeA", [-700, 510]),
    ("WHRelSpdFast",     "K2Node_CallFunction_6",  "OutRangeB", [-700, 590]),
    ("WHTurnRelSpd",     "K2Node_CallFunction_8",  "A",         [-700, 670]),
]:
    v = vg(GA, var, pos)
    run(f"w {var}", *bp("connect_pins", asset_path=ABP, graph_name=GA,
                        source_node=v, source_pin=var, target_node=tn, target_pin=tp), 60)

# allow 함수: 턴 홀드
v = vg("IsWallHandAllowed", "WHTurnBlockHold", [2600, 900])
run("w hold", *bp("connect_pins", asset_path=ABP, graph_name="IsWallHandAllowed",
                  source_node=v, source_pin="WHTurnBlockHold",
                  target_node="K2Node_CallFunction_17", target_pin="A"))

# 상태 게터: Alpha 출력 × 강도 (내부 수학 불변)
GS = "GetWallHandState"
MUL = json.loads(run("mul", *bp("add_node", asset_path=ABP, graph_name=GS,
                                node_type="CallFunction", function_name="Multiply_DoubleDouble",
                                position=[-250, 60]), 60))["id"]
v = vg(GS, "WHIKStrength", [-450, 120])
run("m1", *bp("connect_pins", asset_path=ABP, graph_name=GS,
              source_node="K2Node_VariableGet_2", source_pin="WallHandAlpha",
              target_node=MUL, target_pin="A"))
run("m2", *bp("connect_pins", asset_path=ABP, graph_name=GS,
              source_node=v, source_pin="WHIKStrength", target_node=MUL, target_pin="B"))
run("m3", *bp("connect_pins", asset_path=ABP, graph_name=GS,
              source_node=MUL, source_pin="ReturnValue",
              target_node="K2Node_FunctionResult_0", target_pin="Alpha"))

run("compile", *bp("compile_blueprint", asset_path=ABP), 300)
print("== v2 abp done ==")
