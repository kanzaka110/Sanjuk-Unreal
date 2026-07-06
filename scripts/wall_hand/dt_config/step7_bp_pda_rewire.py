# -*- coding: utf-8 -*-
"""Step7: PC_01_BP를 DT→DataAsset(GetConfig 원콜)로 전환 + 병합 설계 반영.
- alpha = WHBlendT (시간커브 제거), 타겟 = 거리커브(측면 AttachCurve / 정면 FrontAttachCurve)
- 삭제 필드(Standoff/FrontStandoff/Approach/RelFast)는 상수 복원
- 신규: RightHandHeight(측면 타겟 Z), JogOffset.Y(조깅 높이), 정면 전용 램프"""
from mono import bp
import json, sys

BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
G = "UpdateWallHandIK"
DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"

def run(tag, err, out, n=110):
    print(f"[{tag}]", "ERR" if err else "OK", out[:n])
    if err:
        sys.exit(f"STOP {tag}")
    return out

def add(tag, **kw):
    return json.loads(run(tag, *bp("add_node", asset_path=BP, graph_name=G, **kw)))["id"]

def con(tag, sn, sp, tn, tp):
    run(tag, *bp("connect_pins", asset_path=BP, graph_name=G,
                 source_node=sn, source_pin=sp, target_node=tn, target_pin=tp))

def dis(tag, nid, pin):
    err, out = bp("disconnect_pins", asset_path=BP, graph_name=G, node_id=nid, pin_name=pin)
    print(f"[{tag}]", "ERR" if err else "OK", out[:90])

def dflt(tag, nid, pin, val):
    run(tag, *bp("set_pin_default", asset_path=BP, graph_name=G, node_id=nid, pin_name=pin, value=val))

def node(nid):
    return json.loads(run(f"nd:{nid}", *bp("get_node_details", asset_path=BP, graph_name=G, node_id=nid), 0))

# ── 0) 잔여 id 확보: DUR(CF_92.B 소스), MULS(CF_107 InAlphaScaled 소스)
d = node("K2Node_CallFunction_92")
DUR = next(p["connected_to"][0].split(".")[0] for p in d["pins"] if p["name"] == "B")
d = node("K2Node_CallFunction_107")
MULS = next(p["connected_to"][0].split(".")[0] for p in d["pins"] if p["name"] == "InAlphaScaled")
print("DUR =", DUR, "/ MULS =", MULS)

# ── 1) config 변수 + GetConfig 콜
err, out = bp("add_variable", asset_path=BP, name="WallHandConfig",
              type=f"object:{DIR}/PDA_WallHandIKConfig.PDA_WallHandIKConfig_C",
              default_value=f"{DIR}/DA_WallHandIK.DA_WallHandIK", category="WallHandIK")
if err:
    err, out = bp("add_variable", asset_path=BP, name="WallHandConfig",
                  type="object:PDA_WallHandIKConfig_C",
                  default_value=f"{DIR}/DA_WallHandIK.DA_WallHandIK", category="WallHandIK")
print("[var]", "ERR" if err else "OK", out[:130])
if err:
    sys.exit("STOP var")

VGC = add("VGC", node_type="VariableGet", variable_name="WallHandConfig", position=[-2900, -1300])
CFG = add("CFG", node_type="CallFunction", function_name="GetConfig",
          target_class="PDA_WallHandIKConfig_C", position=[-2700, -1300])
con("vgc→cfg", VGC, "WallHandConfig", CFG, "self")
# exec: Entry→CFG→VS_0 (GR 대체)
con("e→cfg", "K2Node_FunctionEntry_0", "then", CFG, "execute")
con("cfg→vs0", CFG, "then", "K2Node_VariableSet_0", "execute")

# ── 2) Vector2D 브레이크 + 신규 노드
BRJ = add("BRJ", node_type="CallFunction", function_name="BreakVector2D", position=[-2900, -600])
BRR = add("BRR", node_type="CallFunction", function_name="BreakVector2D", position=[-2900, -500])
BRS = add("BRS", node_type="CallFunction", function_name="BreakVector2D", position=[-2900, -400])
con("j", CFG, "JogOffset", BRJ, "InVec")
con("r", CFG, "RunOffset", BRR, "InVec")
con("s", CFG, "SprintOffset", BRS, "InVec")
EVS = add("EVS", node_type="CallFunction", function_name="GetFloatValue", target_class="CurveFloat", position=[-2500, -900])
RMF = add("RMF", node_type="CallFunction", function_name="MapRangeClamped", position=[-2700, -750])
EVF = add("EVF", node_type="CallFunction", function_name="GetFloatValue", target_class="CurveFloat", position=[-2500, -750])
STG = add("STG", node_type="CallFunction", function_name="SelectFloat", position=[-2300, -820])
MKR = add("MKR", node_type="CallFunction", function_name="MakeVector", position=[-2500, -300])
ADR = add("ADR", node_type="CallFunction", function_name="Add_VectorVector", position=[-2300, -300])
dflt("rmf-b", RMF, "OutRangeB", "1.0")

# ── 3) 배선 — 램프/커브
con("c1", CFG, "AttachStartDist", "K2Node_CallFunction_21", "InRangeA")
con("c2", CFG, "AttachFullDist", "K2Node_CallFunction_21", "InRangeB")
con("c3", CFG, "AttachCurve", EVS, "self")
con("c4", "K2Node_CallFunction_21", "ReturnValue", EVS, "InTime")
con("c5", "K2Node_Knot_82", "OutputPin", RMF, "Value")
con("c6", CFG, "AttachStartDist", RMF, "InRangeA")
con("c7", CFG, "FrontFullDist", RMF, "InRangeB")
con("c8", CFG, "FrontAttachCurve", EVF, "self")
con("c9", RMF, "ReturnValue", EVF, "InTime")
con("c10", EVF, "ReturnValue", STG, "A")
con("c11", EVS, "ReturnValue", STG, "B")
con("c12", "K2Node_CallFunction_53", "ReturnValue", STG, "bPickA")
con("c13", STG, "ReturnValue", "K2Node_Knot_69", "InputPin")
# SpineLean 램프(CF_0) 상수 복원
dis("d1", "K2Node_CallFunction_0", "InRangeA")
dis("d2", "K2Node_CallFunction_0", "InRangeB")
dflt("d1v", "K2Node_CallFunction_0", "InRangeA", "60.0")
dflt("d2v", "K2Node_CallFunction_0", "InRangeB", "10.0")
# 정면 폭/높이
con("c14", CFG, "FrontHandHalfWidth", "K2Node_CallFunction_26", "B")
con("c15", CFG, "FrontHandHalfWidth", "K2Node_CallFunction_40", "B")
con("c16", CFG, "FrontHandHeight", "K2Node_CallFunction_41", "Z")
con("c17", CFG, "FrontHandHeight", "K2Node_CallFunction_108", "A")
# 이격 상수 복원
dis("d3", "K2Node_CallFunction_101", "A")
dis("d4", "K2Node_CallFunction_101", "B")
dflt("d3v", "K2Node_CallFunction_101", "A", "4.0")
dflt("d4v", "K2Node_CallFunction_101", "B", "2.0")
dis("d5", "K2Node_CallFunction_77", "B")
dflt("d5v", "K2Node_CallFunction_77", "B", "2.5")
# 속도별 오프셋 (Vector2D)
con("c18", BRJ, "X", "K2Node_CallFunction_1", "A")
con("c19", BRJ, "X", "K2Node_CallFunction_109", "A")
con("c20", BRR, "X", "K2Node_CallFunction_30", "A")
con("c21", BRR, "X", "K2Node_CallFunction_110", "A")
con("c22", BRS, "X", "K2Node_CallFunction_64", "A")
con("c23", BRS, "X", "K2Node_CallFunction_111", "A")
con("c24", BRR, "Y", "K2Node_CallFunction_32", "A")
con("c25", BRR, "Y", "K2Node_CallFunction_32", "B")
con("c26", BRS, "Y", "K2Node_CallFunction_31", "A")
con("c27", BRS, "Y", "K2Node_CallFunction_31", "B")
con("c28", BRJ, "Y", "K2Node_Select_2", "SBWalk_Jogging")
# RightHandHeight → 측면 타겟 Z
con("c29", CFG, "RightHandHeight", MKR, "Z")
con("c30", "K2Node_Knot_76", "OutputPin", ADR, "A")
con("c31", MKR, "ReturnValue", ADR, "B")
con("c32", ADR, "ReturnValue", "K2Node_CallFunction_20", "InTargetWorld")
# 블렌드 체인
con("c33", CFG, "TurnReleaseDuration", "K2Node_CallFunction_76", "A")
con("c34", CFG, "ReleaseDuration", "K2Node_CallFunction_76", "B")
con("c35", CFG, "AttachDuration", DUR, "B")
con("c36", "K2Node_VariableGet_6", "WHBlendT", "K2Node_CallFunction_107", "InAlpha")
con("c37", "K2Node_VariableGet_6", "WHBlendT", MULS, "A")
con("c38", CFG, "IKStrengthMax", MULS, "B")
con("c39", CFG, "TurnBlockHold", "K2Node_CallFunction_107", "InTurnBlockHold")
dis("d6", "K2Node_CallFunction_107", "InApproachDist")
dflt("d6v", "K2Node_CallFunction_107", "InApproachDist", "20.0")

# ── 4) 구 DT 플러밍 제거
for nid in ["K2Node_CallFunction_55", "K2Node_BreakStruct_0", "K2Node_VariableGet_7",
            "K2Node_CallFunction_60", "K2Node_CallFunction_95", "K2Node_CallFunction_102",
            "K2Node_CallFunction_105"]:
    err, out = bp("remove_node", asset_path=BP, graph_name=G, node_id=nid)
    print(f"[rm {nid}]", "ERR" if err else "OK", out[:80])
err, out = bp("remove_variable", asset_path=BP, name="WallHandConfigTable")
print("[rm var]", "ERR" if err else "OK", out[:110])

run("compile", *bp("compile_blueprint", asset_path=BP), 600)
print("== step7 done ==")
