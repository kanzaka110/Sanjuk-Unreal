# -*- coding: utf-8 -*-
"""v2 BP: WallHandConfig 변수 + GetConfig 원콜 + 기존 상수 핀 직결 + ABP 푸시 콜.
롤백(7/3) 그래프 기준 — 동작 로직 무변경."""
from mono import bp
import json, sys

BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
G = "UpdateWallHandIK"
DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"

def run(tag, err, out, n=100):
    print(f"[{tag}]", "ERR" if err else "OK", out[:n])
    if err:
        sys.exit(f"STOP {tag}")
    return out

def add(tag, **kw):
    return json.loads(run(tag, *bp("add_node", asset_path=BP, graph_name=G, **kw), 70))["id"]

def con(tag, sn, sp, tn, tp):
    run(tag, *bp("connect_pins", asset_path=BP, graph_name=G,
                 source_node=sn, source_pin=sp, target_node=tn, target_pin=tp), 60)

# 0) config 변수
err, out = bp("add_variable", asset_path=BP, name="WallHandConfig",
              type=f"object:{DIR}/PDA_WallHandIKConfig.PDA_WallHandIKConfig_C",
              default_value=f"{DIR}/DA_WallHandIK.DA_WallHandIK", category="WallHandIK")
if err and "already exists" not in out:
    print("[var] ERR", out[:150]); sys.exit(1)
print("[var] OK")

X, Y = -2600, -1200
VGC = add("VGC", node_type="VariableGet", variable_name="WallHandConfig", position=[X - 250, Y])
CFG = add("CFG", node_type="CallFunction", function_name="GetConfig",
          target_class="PDA_WallHandIKConfig_C", position=[X, Y])
con("vgc→cfg", VGC, "WallHandConfig", CFG, "self")
con("e→cfg", "K2Node_FunctionEntry_0", "then", CFG, "execute")
con("cfg→vs0", CFG, "then", "K2Node_VariableSet_0", "execute")

BRJ = add("BRJ", node_type="CallFunction", function_name="BreakVector2D", position=[X, Y + 300])
BRR = add("BRR", node_type="CallFunction", function_name="BreakVector2D", position=[X, Y + 400])
BRS = add("BRS", node_type="CallFunction", function_name="BreakVector2D", position=[X, Y + 500])
NEGH = add("NEGH", node_type="CallFunction", function_name="Multiply_DoubleDouble", position=[X, Y + 620])
NEGJ = add("NEGJ", node_type="CallFunction", function_name="Multiply_DoubleDouble", position=[X, Y + 700])
NEGR = add("NEGR", node_type="CallFunction", function_name="Multiply_DoubleDouble", position=[X, Y + 780])
NEGS = add("NEGS", node_type="CallFunction", function_name="Multiply_DoubleDouble", position=[X, Y + 860])
MKR = add("MKR", node_type="CallFunction", function_name="MakeVector", position=[X, Y + 960])
ADR = add("ADR", node_type="CallFunction", function_name="Add_VectorVector", position=[X + 200, Y + 960])
CB = add("CB", node_type="CallFunction", function_name="SetWallHandConfig",
         target_class="PC_01_ABP_C", position=[X + 400, Y])
for nid in (NEGH, NEGJ, NEGR, NEGS):
    run(f"neg {nid}", *bp("set_pin_default", asset_path=BP, graph_name=G,
                          node_id=nid, pin_name="B", value="-1.0"), 60)

con("j", CFG, "JogOffset", BRJ, "InVec")
con("r", CFG, "RunOffset", BRR, "InVec")
con("s", CFG, "SprintOffset", BRS, "InVec")
# 거리 램프
con("c1", CFG, "AttachStartDist", "K2Node_CallFunction_21", "InRangeA")
con("c2", CFG, "AttachFullDist", "K2Node_CallFunction_21", "InRangeB")
# 정면 폭/높이
con("c3", CFG, "FrontHandHalfWidth", "K2Node_CallFunction_26", "B")
con("c4", CFG, "FrontHandHalfWidth", "K2Node_CallFunction_40", "B")
con("c5", CFG, "FrontHandHeight", "K2Node_CallFunction_41", "Z")
con("c6", CFG, "FrontHandHeight", NEGH, "A")
con("c7", NEGH, "ReturnValue", "K2Node_CallFunction_34", "Z")
# 속도별 오프셋
con("c8", BRJ, "X", "K2Node_CallFunction_1", "A")
con("c9", BRJ, "X", NEGJ, "A")
con("c10", NEGJ, "ReturnValue", "K2Node_CallFunction_1", "B")
con("c11", BRR, "X", "K2Node_CallFunction_30", "A")
con("c12", BRR, "X", NEGR, "A")
con("c13", NEGR, "ReturnValue", "K2Node_CallFunction_30", "B")
con("c14", BRS, "X", "K2Node_CallFunction_64", "A")
con("c15", BRS, "X", NEGS, "A")
con("c16", NEGS, "ReturnValue", "K2Node_CallFunction_64", "B")
con("c17", BRR, "Y", "K2Node_CallFunction_32", "A")
con("c18", BRR, "Y", "K2Node_CallFunction_32", "B")
con("c19", BRS, "Y", "K2Node_CallFunction_31", "A")
con("c20", BRS, "Y", "K2Node_CallFunction_31", "B")
con("c21", BRJ, "Y", "K2Node_Select_2", "SBWalk_Jogging")
# RightHandHeight → 측면 타겟 Z (기본 0 = 무변화)
con("c22", CFG, "RightHandHeight", MKR, "Z")
con("c23", "K2Node_Knot_76", "OutputPin", ADR, "A")
con("c24", MKR, "ReturnValue", ADR, "B")
con("c25", ADR, "ReturnValue", "K2Node_CallFunction_20", "InTargetWorld")
# ABP 푸시 (캐스트 뒤 — exec 캐스트 교훈)
con("abp→cb", "K2Node_Knot_23", "OutputPin", CB, "self")
con("cast→cb", "K2Node_DynamicCast_0", "then", CB, "execute")
con("cb→cf54", CB, "then", "K2Node_CallFunction_54", "execute")
for src, dst in [("IKStrengthMax", "InWHIKStrength"), ("AttachSpeedStart", "InWHAttachSpdStart"),
                 ("AttachSpeedEnd", "InWHAttachSpdEnd"), ("ReleaseSpeedSlow", "InWHRelSpdSlow"),
                 ("ReleaseSpeedFast", "InWHRelSpdFast"), ("TurnReleaseSpeed", "InWHTurnRelSpd"),
                 ("TurnBlockHold", "InWHTurnBlockHold")]:
    con(f"p {src}", CFG, src, CB, dst)

run("compile", *bp("compile_blueprint", asset_path=BP), 400)
print("== v2 bp done ==")
