# -*- coding: utf-8 -*-
"""Script B 재개 (step8~12): disconnect_pins 시그니처 수정(node_id+pin_name)."""
from mono import bp
import json, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
G = "UpdateWallHandIK"
CFG = "K2Node_CallFunction_55"
BR = {"RWall": "K2Node_BreakStruct_2", "LWall": "K2Node_BreakStruct_3", "FWall": "K2Node_BreakStruct_4"}
BV_F_HAND = "K2Node_CallFunction_125"
SFJY, SUY, SIK_POS = "K2Node_CallFunction_126", "K2Node_CallFunction_127", None


def run(tag, err, out, n=100):
    print(f"[{tag}]", "ERR" if err else "OK", out[:n])
    if err:
        sys.exit(f"STOP {tag}")
    return out


def con(tag, sn, sp, tn, tp):
    run(tag, *bp("connect_pins", asset_path=BP, graph_name=G,
                 source_node=sn, source_pin=sp, target_node=tn, target_pin=tp), 50)


def add(tag, **kw):
    return json.loads(run(tag, *bp("add_node", asset_path=BP, graph_name=G, **kw), 50))["id"]


def dump():
    err, out = bp("get_graph_data", asset_path=BP, graph_name=G)
    assert not err, out[:200]
    return json.loads(out)


g = dump()
member = {}
for name in BR:
    n = next(x for x in g["nodes"] if x["id"] == BR[name])
    for p in n["pins"]:
        if p["direction"] == "output":
            member[(name, p["name"].split("_")[0])] = p["name"]
cfg = next(x for x in g["nodes"] if x["id"] == CFG)
CX, CY = cfg["pos"]

# 8) 구 우손 전용 Y 경로 차단 + CF_97 제거
run("cut-oldY", *bp("disconnect_pins", asset_path=BP, graph_name=G,
                    node_id="K2Node_CallFunction_119", pin_name="A"), 80)
err, out = bp("remove_node", asset_path=BP, graph_name=G, node_id="K2Node_CallFunction_97")
print("[rm-cf97]", "ERR" if err else "OK", out[:80])  # 이미 없으면 무시

# 9) IKStrength 모드 선택
SIK1 = add("sik1", node_type="CallFunction", function_name="SelectFloat", position=[CX + 820, CY + 940])
con("ik-R", BR["RWall"], member[("RWall", "IKStrength")], SIK1, "A")
con("ik-L", BR["LWall"], member[("LWall", "IKStrength")], SIK1, "B")
con("ik-b", "K2Node_Knot_15", "OutputPin", SIK1, "bPickA")
SIK2 = add("sik2", node_type="CallFunction", function_name="SelectFloat", position=[CX + 980, CY + 940])
con("ik-F", BR["FWall"], member[("FWall", "IKStrength")], SIK2, "A")
con("ik-side", SIK1, "ReturnValue", SIK2, "B")
con("ik-bf", "K2Node_Knot_80", "OutputPin", SIK2, "bPickA")
con("ik→knot2", SIK2, "ReturnValue", "K2Node_Knot_2", "InputPin")

# 10) 거리 모드 선택 ×2
for tag, fld, knot, yoff in (("sd", "AttachStartDist", "K2Node_Knot_77", 1060),
                             ("fd", "AttachFullDist", "K2Node_Knot_79", 1180)):
    S1 = add(f"{tag}1", node_type="CallFunction", function_name="SelectFloat", position=[CX + 820, CY + yoff])
    con(f"{tag}-R", BR["RWall"], member[("RWall", fld)], S1, "A")
    con(f"{tag}-L", BR["LWall"], member[("LWall", fld)], S1, "B")
    con(f"{tag}-b", "K2Node_Knot_15", "OutputPin", S1, "bPickA")
    S2 = add(f"{tag}2", node_type="CallFunction", function_name="SelectFloat", position=[CX + 980, CY + yoff])
    con(f"{tag}-F", BR["FWall"], member[("FWall", fld)], S2, "A")
    con(f"{tag}-side", S1, "ReturnValue", S2, "B")
    con(f"{tag}-bf", "K2Node_Knot_80", "OutputPin", S2, "bPickA")
    con(f"{tag}→knot", S2, "ReturnValue", knot, "InputPin")

# 11) 정면 손: 신규 BV(CF_125) → 기존 Knot 4개, 구 CF_96 제거
con("fw-x1", BV_F_HAND, "X", "K2Node_Knot_92", "InputPin")
con("fw-x2", BV_F_HAND, "X", "K2Node_Knot_93", "InputPin")
con("fw-y1", BV_F_HAND, "Y", "K2Node_Knot_74", "InputPin")
con("fw-y2", BV_F_HAND, "Y", "K2Node_Knot_90", "InputPin")
err, out = bp("remove_node", asset_path=BP, graph_name=G, node_id="K2Node_CallFunction_96")
print("[rm-cf96]", "ERR" if err else "OK", out[:80])

run("bp-compile2", *bp("compile_blueprint", asset_path=BP), 300)

# 12) 최종 스캔
g = dump()
cfg = next(n for n in g["nodes"] if n["id"] == CFG)
bad = [p["name"] for p in cfg["pins"] if p["direction"] == "output"
       and p["name"] != "then" and not p.get("connected_to")]
print("미연결 출력:", bad if bad else "없음")
for nid in ("K2Node_CallFunction_1", "K2Node_CallFunction_30", "K2Node_CallFunction_64",
            "K2Node_CallFunction_32", "K2Node_CallFunction_31", "K2Node_CallFunction_99",
            "K2Node_CallFunction_98", SFJY, SUY, SIK1, SIK2):
    n = next(x for x in g["nodes"] if x["id"] == nid)
    holes = [p["name"] for p in n["pins"] if p["direction"] == "input"
             and p["name"] in ("A", "B", "bPickA") and not p.get("connected_to")]
    if holes:
        print(f"!! {nid} 미연결 입력: {holes}")
print("== Script B2 done ==")
