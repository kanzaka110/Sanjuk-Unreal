# -*- coding: utf-8 -*-
"""Step3b: FIC 실패 지점부터 재개. 기생성 ID 고정."""
from mono import bp
import json, sys

ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
G = "SetSmoothedWallHandAlpha"
DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"

GR, BK = "K2Node_CallFunction_17", "K2Node_BreakStruct_0"
SAP, STH, SBT, SAS = "K2Node_VariableSet_3", "K2Node_VariableSet_4", "K2Node_VariableSet_6", "K2Node_VariableSet_7"
GBT1, GBT2 = "K2Node_VariableGet_0", "K2Node_VariableGet_5"
FIC = "K2Node_CallFunction_19"

def run(tag, err, out, n=160):
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

DIV = add("DIV", node_type="CallFunction", function_name="Divide_DoubleDouble", position=[-1000, 0])
DUR = add("DUR", node_type="CallFunction", function_name="SelectFloat", position=[-1150, 30])
EVA = add("EVA", node_type="CallFunction", function_name="GetFloatValue", target_class="CurveFloat", position=[-350, 150])
EVR = add("EVR", node_type="CallFunction", function_name="GetFloatValue", target_class="CurveFloat", position=[-350, 300])
ASEL = add("ASEL", node_type="CallFunction", function_name="SelectFloat", position=[-150, 100])
MULS = add("MULS", node_type="CallFunction", function_name="Multiply_DoubleDouble", position=[350, 200])
print("IDS:", json.dumps({"DIV": DIV, "DUR": DUR, "EVA": EVA, "EVR": EVR, "ASEL": ASEL, "MULS": MULS}))

run("tbl", *bp("set_pin_default", asset_path=ABP, graph_name=G, node_id=GR,
               pin_name="Table", value=f"{DIR}/DT_WallHandIK.DT_WallHandIK"))
run("row", *bp("set_pin_default", asset_path=ABP, graph_name=G, node_id=GR,
               pin_name="RowName", value="Default"))

out = run("bkpins", *bp("get_node_details", asset_path=ABP, graph_name=G, node_id=BK), 0)
bkpins = {p["name"].split("_")[0]: p["name"] for p in json.loads(out)["pins"] if p["direction"] == "output"}
print("BK fields:", sorted(bkpins.keys()))

con("row→bk", GR, "OutRow", BK, "S_WallHandIKConfig")
con("bk→sap", BK, bkpins["ApproachOffsetDist"], SAP, "WHApproachDist")
con("bk→sth", BK, bkpins["TurnBlockHold"], STH, "WHTurnBlockHold")
con("cf8→dur", "K2Node_CallFunction_8", "ReturnValue", DUR, "A")
con("bk→durB", BK, bkpins["AttachDuration"], DUR, "B")
con("cf1→durP", "K2Node_CallFunction_1", "ReturnValue", DUR, "bPickA")
run("divA", *bp("set_pin_default", asset_path=ABP, graph_name=G, node_id=DIV, pin_name="A", value="1.0"))
con("dur→div", DUR, "ReturnValue", DIV, "B")
con("gbt1→fic", GBT1, "WHBlendT", FIC, "Current")
con("tgt→fic", "K2Node_VariableGet_1", "WallHandAlphaTarget", FIC, "Target")
con("dt→fic", "K2Node_VariableGet_2", "Delta Time", FIC, "DeltaTime")
con("div→fic", DIV, "ReturnValue", FIC, "InterpSpeed")
con("fic→sbt", FIC, "ReturnValue", SBT, "WHBlendT")
con("gbt1→cf1B", GBT1, "WHBlendT", "K2Node_CallFunction_1", "B")
con("bk→cf8A", BK, bkpins["TurnReleaseDuration"], "K2Node_CallFunction_8", "A")
con("bk→cf6a", BK, bkpins["ReleaseDuration"], "K2Node_CallFunction_6", "OutRangeA")
con("bk→cf6b", BK, bkpins["ReleaseDurationFast"], "K2Node_CallFunction_6", "OutRangeB")
con("bk→evaS", BK, bkpins["AttachCurve"], EVA, "self")
con("gbt2→eva", GBT2, "WHBlendT", EVA, "InTime")
con("bk→evrS", BK, bkpins["ReleaseCurve"], EVR, "self")
con("gbt2→evr", GBT2, "WHBlendT", EVR, "InTime")
con("evr→aselA", EVR, "ReturnValue", ASEL, "A")
con("eva→aselB", EVA, "ReturnValue", ASEL, "B")
con("cf1→aselP", "K2Node_CallFunction_1", "ReturnValue", ASEL, "bPickA")
con("asel→vs0", ASEL, "ReturnValue", "K2Node_VariableSet_0", "WallHandAlpha")
con("asel→mul", ASEL, "ReturnValue", MULS, "A")
con("bk→mulB", BK, bkpins["IKStrengthMax"], MULS, "B")
con("mul→sas", MULS, "ReturnValue", SAS, "WHAlphaScaled")

con("e→gr", "K2Node_FunctionEntry_0", "then", GR, "execute")
con("gr→sap", GR, "then", SAP, "execute")
con("sap→sth", SAP, "then", STH, "execute")
con("sth→sbt", STH, "then", SBT, "execute")
con("sbt→vs0", SBT, "then", "K2Node_VariableSet_0", "execute")
con("vs0→sas", "K2Node_VariableSet_0", "then", SAS, "execute")
con("sas→vs1", SAS, "then", "K2Node_VariableSet_1", "execute")

for nid in ["K2Node_CallFunction_0", "K2Node_CallFunction_2", "K2Node_CallFunction_16",
            "K2Node_CallFunction_3", "K2Node_CallFunction_4", "K2Node_CallFunction_5",
            "K2Node_Knot_0"]:
    err, out = bp("remove_node", asset_path=ABP, graph_name=G, node_id=nid)
    print(f"[rm {nid}]", "ERR" if err else "OK", out[:100])

print("== step3b done ==")
