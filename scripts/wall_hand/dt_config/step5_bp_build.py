# -*- coding: utf-8 -*-
"""Step5: PC_01_BP UpdateWallHandIK — DT 읽기 + 커브 블렌드(게임스레드) + 상수 핀 DT화.
Entry→GR→Set WHBlendT→SetWallHandBlend(ABP)→기존체인(VS_0)."""
from mono import bp
import json, sys

BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
G = "UpdateWallHandIK"
DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"

def run(tag, err, out, n=140):
    print(f"[{tag}]", "ERR" if err else "OK", out[:n])
    if err:
        sys.exit(f"STOP at {tag}")
    return out

def add(tag, **kw):
    out = run(tag, *bp("add_node", asset_path=BP, graph_name=G, **kw))
    return json.loads(out)["id"]

def con(tag, sn, sp, tn, tp):
    run(tag, *bp("connect_pins", asset_path=BP, graph_name=G,
                 source_node=sn, source_pin=sp, target_node=tn, target_pin=tp))

def dflt(tag, nid, pin, val):
    run(tag, *bp("set_pin_default", asset_path=BP, graph_name=G, node_id=nid, pin_name=pin, value=val))

# ── 0) BP 변수 WHBlendT
err, out = bp("add_variable", asset_path=BP, name="WHBlendT", type="float",
              default_value="0.0", category="WallHandIK")
print("[var]", "ERR" if err else "OK", out[:150])

# ── 1) 노드 생성 (좌상단 빈 영역)
X, Y = -2600, -1200
GR   = add("GR",  node_type="CallFunction", function_name="GetDataTableRowFromName",
           target_class="DataTableFunctionLibrary", position=[X, Y])
BK   = add("BK",  node_type="BreakStruct", struct_type=f"{DIR}/S_WallHandIKConfig.S_WallHandIKConfig",
           position=[X, Y + 250])
GS   = add("GS",  node_type="CallFunction", function_name="GetWallHandState",
           target_class="PC_01_ABP_C", position=[X, Y + 900])
GBT1 = add("GBT1", node_type="VariableGet", variable_name="WHBlendT", position=[X + 150, Y + 1100])
GBT2 = add("GBT2", node_type="VariableGet", variable_name="WHBlendT", position=[X + 900, Y + 1100])
LESS = add("LESS", node_type="CallFunction", function_name="Less_DoubleDouble", position=[X + 300, Y + 950])
GT   = add("GT",  node_type="CallFunction", function_name="Greater_DoubleDouble", position=[X + 300, Y + 1050])
MAPD = add("MAPD", node_type="CallFunction", function_name="MapRangeClamped", position=[X + 300, Y + 700])
DURR = add("DURR", node_type="CallFunction", function_name="SelectFloat", position=[X + 500, Y + 800])
DUR  = add("DUR", node_type="CallFunction", function_name="SelectFloat", position=[X + 650, Y + 900])
DIV  = add("DIV", node_type="CallFunction", function_name="Divide_DoubleDouble", position=[X + 800, Y + 950])
GWDS = add("GWDS", node_type="CallFunction", function_name="GetWorldDeltaSeconds", position=[X + 800, Y + 1050])
FIC  = add("FIC", node_type="CallFunction", function_name="FInterpTo_Constant", position=[X + 950, Y + 900])
SBT  = add("SBT", node_type="VariableSet", variable_name="WHBlendT", position=[X + 300, Y])
EVA  = add("EVA", node_type="CallFunction", function_name="GetFloatValue", target_class="CurveFloat", position=[X + 1100, Y + 1100])
EVR  = add("EVR", node_type="CallFunction", function_name="GetFloatValue", target_class="CurveFloat", position=[X + 1100, Y + 1250])
ASEL = add("ASEL", node_type="CallFunction", function_name="SelectFloat", position=[X + 1300, Y + 1100])
MULS = add("MULS", node_type="CallFunction", function_name="Multiply_DoubleDouble", position=[X + 1450, Y + 1200])
CB   = add("CB",  node_type="CallFunction", function_name="SetWallHandBlend",
           target_class="PC_01_ABP_C", position=[X + 550, Y])
NEGH = add("NEGH", node_type="CallFunction", function_name="Multiply_DoubleDouble", position=[X, Y + 1500])
NEGJ = add("NEGJ", node_type="CallFunction", function_name="Multiply_DoubleDouble", position=[X, Y + 1600])
NEGR = add("NEGR", node_type="CallFunction", function_name="Multiply_DoubleDouble", position=[X, Y + 1700])
NEGS = add("NEGS", node_type="CallFunction", function_name="Multiply_DoubleDouble", position=[X, Y + 1800])
print("IDS:", json.dumps(dict(GR=GR, BK=BK, GS=GS, SBT=SBT, CB=CB, FIC=FIC)))

# ── 2) 디폴트
dflt("tbl", GR, "Table", f"{DIR}/DT_WallHandIK.DT_WallHandIK")
dflt("row", GR, "RowName", "Default")
dflt("gt-b", GT, "B", "0.0")
dflt("mapd-a", MAPD, "InRangeA", "100.0")
dflt("mapd-b", MAPD, "InRangeB", "450.0")
dflt("div-a", DIV, "A", "1.0")
for nid in (NEGH, NEGJ, NEGR, NEGS):
    dflt(f"neg-{nid}", nid, "B", "-1.0")

# ── 3) Break 핀 매핑
out = run("bkpins", *bp("get_node_details", asset_path=BP, graph_name=G, node_id=BK), 0)
K = {p["name"].split("_")[0]: p["name"] for p in json.loads(out)["pins"] if p["direction"] == "output"}

# ── 4) 블렌드 체인 배선
con("row→bk", GR, "OutRow", BK, "S_WallHandIKConfig")
con("abp→gs", "K2Node_Knot_23", "OutputPin", GS, "self")
con("abp→cb", "K2Node_Knot_23", "OutputPin", CB, "self")
con("gs→less", GS, "AlphaTarget", LESS, "A")
con("gbt1→less", GBT1, "WHBlendT", LESS, "B")
con("gs→gt", GS, "TurnBlockT", GT, "A")
con("spd→mapd", "K2Node_CallFunction_51", "ReturnValue", MAPD, "Value")
con("bk→mapdA", BK, K["ReleaseDuration"], MAPD, "OutRangeA")
con("bk→mapdB", BK, K["ReleaseDurationFast"], MAPD, "OutRangeB")
con("bk→durrA", BK, K["TurnReleaseDuration"], DURR, "A")
con("mapd→durrB", MAPD, "ReturnValue", DURR, "B")
con("gt→durrP", GT, "ReturnValue", DURR, "bPickA")
con("durr→durA", DURR, "ReturnValue", DUR, "A")
con("bk→durB", BK, K["AttachDuration"], DUR, "B")
con("less→durP", LESS, "ReturnValue", DUR, "bPickA")
con("dur→div", DUR, "ReturnValue", DIV, "B")
con("gbt1→fic", GBT1, "WHBlendT", FIC, "Current")
con("gs→fic", GS, "AlphaTarget", FIC, "Target")
con("gwds→fic", GWDS, "ReturnValue", FIC, "DeltaTime")
con("div→fic", DIV, "ReturnValue", FIC, "InterpSpeed")
con("fic→sbt", FIC, "ReturnValue", SBT, "WHBlendT")
con("bk→evaS", BK, K["AttachCurve"], EVA, "self")
con("gbt2→eva", GBT2, "WHBlendT", EVA, "InTime")
con("bk→evrS", BK, K["ReleaseCurve"], EVR, "self")
con("gbt2→evr", GBT2, "WHBlendT", EVR, "InTime")
con("evr→aselA", EVR, "ReturnValue", ASEL, "A")
con("eva→aselB", EVA, "ReturnValue", ASEL, "B")
con("less→aselP", LESS, "ReturnValue", ASEL, "bPickA")
con("asel→cb1", ASEL, "ReturnValue", CB, "InAlpha")
con("asel→mul", ASEL, "ReturnValue", MULS, "A")
con("bk→mulB", BK, K["IKStrengthMax"], MULS, "B")
con("mul→cb2", MULS, "ReturnValue", CB, "InAlphaScaled")
con("bk→cb3", BK, K["ApproachOffsetDist"], CB, "InApproachDist")
con("bk→cb4", BK, K["TurnBlockHold"], CB, "InTurnBlockHold")

# ── 5) exec 스플라이스: Entry→GR→SBT→CB→VS_0(기존)
con("e→gr", "K2Node_FunctionEntry_0", "then", GR, "execute")
con("gr→sbt", GR, "then", SBT, "execute")
con("sbt→cb", SBT, "then", CB, "execute")
con("cb→vs0", CB, "then", "K2Node_VariableSet_0", "execute")

# ── 6) 기존 상수 핀 → DT 배선
con("d1", BK, K["AttachStartDist"], "K2Node_CallFunction_21", "InRangeA")
con("d2", BK, K["AttachFullDist"], "K2Node_CallFunction_21", "InRangeB")
con("d3", BK, K["AttachStartDist"], "K2Node_CallFunction_0", "InRangeA")
con("d4", BK, K["FrontFullDist"], "K2Node_CallFunction_0", "InRangeB")
con("d5", BK, K["StandoffR"], "K2Node_CallFunction_101", "A")
con("d6", BK, K["StandoffL"], "K2Node_CallFunction_101", "B")
con("d7", BK, K["FrontHandHalfWidth"], "K2Node_CallFunction_26", "B")
con("d8", BK, K["FrontHandHalfWidth"], "K2Node_CallFunction_40", "B")
con("d9", BK, K["FrontHandHeight"], "K2Node_CallFunction_41", "Z")
con("d10", BK, K["FrontHandHeight"], NEGH, "A")
con("d11", NEGH, "ReturnValue", "K2Node_CallFunction_34", "Z")
con("d12", BK, K["FrontStandoff"], "K2Node_CallFunction_77", "B")
con("d13", BK, K["FwdOffsetJog"], "K2Node_CallFunction_1", "A")
con("d14", BK, K["FwdOffsetJog"], NEGJ, "A")
con("d15", NEGJ, "ReturnValue", "K2Node_CallFunction_1", "B")
con("d16", BK, K["FwdOffsetRun"], "K2Node_CallFunction_30", "A")
con("d17", BK, K["FwdOffsetRun"], NEGR, "A")
con("d18", NEGR, "ReturnValue", "K2Node_CallFunction_30", "B")
con("d19", BK, K["FwdOffsetSprint"], "K2Node_CallFunction_64", "A")
con("d20", BK, K["FwdOffsetSprint"], NEGS, "A")
con("d21", NEGS, "ReturnValue", "K2Node_CallFunction_64", "B")
con("d22", BK, K["HeightOffsetRun"], "K2Node_CallFunction_32", "A")
con("d23", BK, K["HeightOffsetRun"], "K2Node_CallFunction_32", "B")
con("d24", BK, K["HeightOffsetSprint"], "K2Node_CallFunction_31", "A")
con("d25", BK, K["HeightOffsetSprint"], "K2Node_CallFunction_31", "B")

run("compile", *bp("compile_blueprint", asset_path=BP), 700)
print("== step5 done ==")
