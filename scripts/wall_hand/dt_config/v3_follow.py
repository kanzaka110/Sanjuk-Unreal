# -*- coding: utf-8 -*-
"""본 스웨이 팔로우 (측면 전용, Z만): 지정 본의 Z 흔들림(저역 기준선 대비)을 손 타겟에 Pct% 전달.
MKR.Z = RightHandHeight + (boneZ − baselineZ) × Pct. 기본 Pct 0 = 무변화."""
from mono import bp
import json, sys

BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
G = "UpdateWallHandIK"

def run(tag, err, out, n=90):
    print(f"[{tag}]", "ERR" if err else "OK", out[:n])
    if err:
        sys.exit(f"STOP {tag}")
    return out

def add(tag, **kw):
    return json.loads(run(tag, *bp("add_node", asset_path=BP, graph_name=G, **kw), 60))["id"]

def con(tag, sn, sp, tn, tp):
    run(tag, *bp("connect_pins", asset_path=BP, graph_name=G,
                 source_node=sn, source_pin=sp, target_node=tn, target_pin=tp), 50)

# 0) 리컴파일로 CFG 신규 핀 반영 + 기준선 변수
run("recompile", *bp("compile_blueprint", asset_path=BP), 100)
err, out = bp("add_variable", asset_path=BP, name="WHFollowBaseZ", type="float",
              default_value="0.0", category="WallHandIK")
print("[var]", "ERR" if err else "OK", out[:80])

CFG = "K2Node_CallFunction_55"
X, Y = -2300, -700
# 1) 상태 판정 + 본/비율 선택
GT = add("GT", node_type="CallFunction", function_name="Greater_DoubleDouble", position=[X, Y])
run("gt-b", *bp("set_pin_default", asset_path=BP, graph_name=G, node_id=GT, pin_name="B", value="80.0"))
con("spd→gt", "K2Node_CallFunction_51", "ReturnValue", GT, "A")
PCT = add("PCT", node_type="CallFunction", function_name="SelectFloat", position=[X + 150, Y + 80])
con("p1", CFG, "MoveFollowPct", PCT, "A")
con("p2", CFG, "IdleFollowPct", PCT, "B")
con("p3", GT, "ReturnValue", PCT, "bPickA")
# 본 위치: idle/move 각각 GetSocketLocation → SelectVector (SelectName 회피)
MESH = add("MESH", node_type="VariableGet", variable_name="Mesh", position=[X, Y + 200])
LI = add("LI", node_type="CallFunction", function_name="GetSocketLocation",
         target_class="SceneComponent", position=[X + 150, Y + 200])
LM = add("LM", node_type="CallFunction", function_name="GetSocketLocation",
         target_class="SceneComponent", position=[X + 150, Y + 300])
con("m→li", MESH, "Mesh", LI, "self")
con("m→lm", MESH, "Mesh", LM, "self")
con("b1", CFG, "IdleFollowBone", LI, "InSocketName")
con("b2", CFG, "MoveFollowBone", LM, "InSocketName")
LSEL = add("LSEL", node_type="CallFunction", function_name="SelectVector", position=[X + 350, Y + 250])
con("l1", LM, "ReturnValue", LSEL, "A")
con("l2", LI, "ReturnValue", LSEL, "B")
con("l3", GT, "ReturnValue", LSEL, "bPickA")
BRK = add("BRK", node_type="CallFunction", function_name="BreakVector", position=[X + 500, Y + 250])
con("brk", LSEL, "ReturnValue", BRK, "InVec")
# 2) 저역 기준선 (FInterpTo 2.0, dt 고정 — 기존 CF_29 패턴)
GBASE = add("GBASE", node_type="VariableGet", variable_name="WHFollowBaseZ", position=[X + 500, Y + 380])
FIB = add("FIB", node_type="CallFunction", function_name="FInterpTo", position=[X + 650, Y + 320])
run("fib-dt", *bp("set_pin_default", asset_path=BP, graph_name=G, node_id=FIB, pin_name="DeltaTime", value="0.016667"))
run("fib-sp", *bp("set_pin_default", asset_path=BP, graph_name=G, node_id=FIB, pin_name="InterpSpeed", value="2.0"))
con("f1", GBASE, "WHFollowBaseZ", FIB, "Current")
con("f2", BRK, "Z", FIB, "Target")
SBASE = add("SBASE", node_type="VariableSet", variable_name="WHFollowBaseZ", position=[X + 850, Y + 320])
con("f3", FIB, "ReturnValue", SBASE, "WHFollowBaseZ")
# exec: CB(SetWallHandConfig) 뒤 스플라이스 — CB=CF_95, CB.then→CF_54
con("cb→sb", "K2Node_CallFunction_95", "then", SBASE, "execute")
con("sb→54", SBASE, "then", "K2Node_CallFunction_54", "execute")
# 3) sway = (Z − base) × pct → MKR.Z = RightHandHeight + sway
SUB = add("SUB", node_type="CallFunction", function_name="Subtract_DoubleDouble", position=[X + 700, Y + 150])
con("s1", BRK, "Z", SUB, "A")
con("s2", GBASE, "WHFollowBaseZ", SUB, "B")
MUL = add("MUL", node_type="CallFunction", function_name="Multiply_DoubleDouble", position=[X + 850, Y + 150])
con("s3", SUB, "ReturnValue", MUL, "A")
con("s4", PCT, "ReturnValue", MUL, "B")
ADDF = add("ADDF", node_type="CallFunction", function_name="Add_DoubleDouble", position=[X + 1000, Y + 100])
con("s5", CFG, "RightHandHeight", ADDF, "A")
con("s6", MUL, "ReturnValue", ADDF, "B")
# MKR 찾기: RightHandHeight의 기존 소비자(MakeVector)
d = json.loads(run("cfgpins", *bp("get_node_details", asset_path=BP, graph_name=G, node_id=CFG), 0))
rhh = next(p for p in d["pins"] if p["name"] == "RightHandHeight")
MKR = next(c.split(".")[0] for c in rhh["connected_to"] if c.split(".")[0] != ADDF)
print("MKR =", MKR)
con("s7", ADDF, "ReturnValue", MKR, "Z")
run("compile", *bp("compile_blueprint", asset_path=BP), 300)
print("== v3 follow done ==")
