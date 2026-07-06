# -*- coding: utf-8 -*-
"""Step3: SetSmoothedWallHandAlpha 커브 기반 리팩터.
구조: Entry→GetRow→Set WHApproachDist→Set WHTurnBlockHold→Set WHBlendT→Set WallHandAlpha→Set WHAlphaScaled→(기존 WHEngageR...)
알파 = Select(ReleaseCurve(T), AttachCurve(T), releasing) — CF_1/CF_6/CF_8 재활용."""
from mono import bp
import json, sys

ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
G = "SetSmoothedWallHandAlpha"
DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"

def run(tag, err, out, n=200):
    print(f"[{tag}]", "ERR" if err else "OK", out[:n])
    if err:
        sys.exit(f"STOP at {tag}")
    return out

def add(tag, **kw):
    out = run(tag, *bp("add_node", asset_path=ABP, graph_name=G, **kw))
    return json.loads(out)["id"]

def con(tag, sn, sp, tn, tp):
    run(tag, *bp("connect_pins", asset_path=ABP, graph_name=G,
                 source_node=sn, source_pin=sp, target_node=tn, target_pin=tp))

def pins_of(node_id):
    out = run(f"pins:{node_id}", *bp("get_node_details", asset_path=ABP, graph_name=G, node_id=node_id), 0)
    return json.loads(out)["pins"]

# ── 1) 신규 노드
GR  = add("GR",  node_type="CallFunction", function_name="GetDataTableRowFromName",
          target_class="DataTableFunctionLibrary", position=[-1400, -400])
BK  = add("BK",  node_type="BreakStruct", struct_type=f"{DIR}/S_WallHandIKConfig.S_WallHandIKConfig",
          position=[-1400, -150])
SAP = add("SAP", node_type="VariableSet", variable_name="WHApproachDist",  position=[-1100, -400])
STH = add("STH", node_type="VariableSet", variable_name="WHTurnBlockHold", position=[-900, -400])
SBT = add("SBT", node_type="VariableSet", variable_name="WHBlendT",        position=[-700, -400])
SAS = add("SAS", node_type="VariableSet", variable_name="WHAlphaScaled",   position=[500, 16])
GBT1 = add("GBT1", node_type="VariableGet", variable_name="WHBlendT", position=[-1100, 100])  # pre-set 읽기(방향판정/FIC)
GBT2 = add("GBT2", node_type="VariableGet", variable_name="WHBlendT", position=[-500, 250])   # post-set 읽기(커브 평가)
FIC = add("FIC", node_type="CallFunction", function_name="FInterpConstantTo", position=[-850, -150])
DIV = add("DIV", node_type="CallFunction", function_name="Divide_DoubleDouble", position=[-1000, 0])
DUR = add("DUR", node_type="CallFunction", function_name="SelectFloat", position=[-1150, 30])
EVA = add("EVA", node_type="CallFunction", function_name="GetFloatValue", target_class="CurveFloat", position=[-350, 150])
EVR = add("EVR", node_type="CallFunction", function_name="GetFloatValue", target_class="CurveFloat", position=[-350, 300])
ASEL = add("ASEL", node_type="CallFunction", function_name="SelectFloat", position=[-150, 100])
MULS = add("MULS", node_type="CallFunction", function_name="Multiply_DoubleDouble", position=[350, 200])

# ── 2) GetRow 디폴트
run("tbl", *bp("set_pin_default", asset_path=ABP, graph_name=G, node_id=GR,
               pin_name="Table", value=f"{DIR}/DT_WallHandIK.DT_WallHandIK"))
run("row", *bp("set_pin_default", asset_path=ABP, graph_name=G, node_id=GR,
               pin_name="RowName", value="Default"))

# ── 3) Break 핀 이름 해석 (mangled)
bkpins = {p["name"].split("_")[0]: p["name"] for p in pins_of(BK) if p["direction"] == "output"}
print("BK fields:", sorted(bkpins.keys()))

# ── 4) 데이터 배선
con("row→bk", GR, "OutRow", BK, "S_WallHandIKConfig")
con("bk→sap", BK, bkpins["ApproachOffsetDist"], SAP, "WHApproachDist")
con("bk→sth", BK, bkpins["TurnBlockHold"], STH, "WHTurnBlockHold")
# duration 선택: DUR = Select(A=릴리즈dur(CF_8 재활용), B=AttachDuration, bPickA=releasing(CF_1))
con("cf8→dur", "K2Node_CallFunction_8", "ReturnValue", DUR, "A")
con("bk→durB", BK, bkpins["AttachDuration"], DUR, "B")
con("cf1→durP", "K2Node_CallFunction_1", "ReturnValue", DUR, "bPickA")
# DIV = 1.0 / DUR
run("divA", *bp("set_pin_default", asset_path=ABP, graph_name=G, node_id=DIV, pin_name="A", value="1.0"))
con("dur→div", DUR, "ReturnValue", DIV, "B")
# FIC = FInterpConstantTo(WHBlendT, AlphaTarget, dt, 1/dur) → Set WHBlendT
con("gbt1→fic", GBT1, "WHBlendT", FIC, "Current")
con("tgt→fic", "K2Node_VariableGet_1", "WallHandAlphaTarget", FIC, "Target")
con("dt→fic", "K2Node_VariableGet_2", "Delta Time", FIC, "DeltaTime")
con("div→fic", DIV, "ReturnValue", FIC, "InterpSpeed")
con("fic→sbt", FIC, "ReturnValue", SBT, "WHBlendT")
# CF_1 방향판정 B핀: alpha(Knot_0) → WHBlendT(pre-set)
con("gbt1→cf1B", GBT1, "WHBlendT", "K2Node_CallFunction_1", "B")
# CF_8.A: 28 상수 → TurnReleaseDuration / CF_6 OutRange → Release durations
con("bk→cf8A", BK, bkpins["TurnReleaseDuration"], "K2Node_CallFunction_8", "A")
con("bk→cf6a", BK, bkpins["ReleaseDuration"], "K2Node_CallFunction_6", "OutRangeA")
con("bk→cf6b", BK, bkpins["ReleaseDurationFast"], "K2Node_CallFunction_6", "OutRangeB")
# 커브 평가 (post-set WHBlendT)
con("bk→evaS", BK, bkpins["AttachCurve"], EVA, "self")
con("gbt2→eva", GBT2, "WHBlendT", EVA, "InTime")
con("bk→evrS", BK, bkpins["ReleaseCurve"], EVR, "self")
con("gbt2→evr", GBT2, "WHBlendT", EVR, "InTime")
# ASEL = Select(A=release평가, B=attach평가, bPickA=releasing) → Set WallHandAlpha
con("evr→aselA", EVR, "ReturnValue", ASEL, "A")
con("eva→aselB", EVA, "ReturnValue", ASEL, "B")
con("cf1→aselP", "K2Node_CallFunction_1", "ReturnValue", ASEL, "bPickA")
con("asel→vs0", ASEL, "ReturnValue", "K2Node_VariableSet_0", "WallHandAlpha")
# 강도 스케일
con("asel→mul", ASEL, "ReturnValue", MULS, "A")
con("bk→mulB", BK, bkpins["IKStrengthMax"], MULS, "B")
con("mul→sas", MULS, "ReturnValue", SAS, "WHAlphaScaled")

# ── 5) exec 스플라이스: Entry→GR→SAP→STH→SBT→VS_0→SAS→VS_1(기존)
con("e→gr",  "K2Node_FunctionEntry_0", "then", GR, "execute")
con("gr→sap", GR, "then", SAP, "execute")
con("sap→sth", SAP, "then", STH, "execute")
con("sth→sbt", STH, "then", SBT, "execute")
con("sbt→vs0", SBT, "then", "K2Node_VariableSet_0", "execute")
con("vs0→sas", "K2Node_VariableSet_0", "then", SAS, "execute")
con("sas→vs1", SAS, "then", "K2Node_VariableSet_1", "execute")

# ── 6) 죽은 노드 제거 (구 FInterpTo 체인)
for nid in ["K2Node_CallFunction_0", "K2Node_CallFunction_2", "K2Node_CallFunction_16",
            "K2Node_CallFunction_3", "K2Node_CallFunction_4", "K2Node_CallFunction_5",
            "K2Node_Knot_0"]:
    err, out = bp("remove_node", asset_path=ABP, graph_name=G, node_id=nid)
    print(f"[rm {nid}]", "ERR" if err else "OK", out[:120])

print("== step3 done ==")
