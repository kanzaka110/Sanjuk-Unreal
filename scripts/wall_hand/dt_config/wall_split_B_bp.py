# -*- coding: utf-8 -*-
"""벽별 설정 분리 Script B: PC_01_BP UpdateWallHandIK 재배선.
BreakStruct×3(R/L/F) + BreakV2D×9 → 기존 bRight ± Select 입력 교체(R/L 독립값),
좌손 Y 버그 수정(위 오프셋을 CF_84 분기 전 CF_90→Knot_34 사이 스플라이스),
IKStrength/거리 모드 2단 Select(bFront→F, bRight→R/L)."""
from mono import bp
import json, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"
BP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
G = "UpdateWallHandIK"
SIDE = f"{DIR}/S_WallHandSideConfig.S_WallHandSideConfig"
FRONT = f"{DIR}/S_WallHandFrontConfig.S_WallHandFrontConfig"

KEEP = [  # 재생성 후 생존 확인 대상 (src_pin, target_node, target_pin)
    ("AttachSpeed", "K2Node_CallFunction_102", "InVec"),
    ("ReleaseSpeed", "K2Node_CallFunction_105", "InVec"),
    ("TurnReleaseSpeed", "K2Node_Knot_53", "InputPin"),
    ("SpineLeanMaxDeg", "K2Node_CallFunction_120", "A"),
    ("ElbowAngleDeg", "K2Node_CallFunction_122", "A"),
    ("TurnBlockHold", "K2Node_Knot_54", "InputPin"),
    ("IdleFollow", "K2Node_BreakStruct_0", "S_WallHandFollow"),
    ("MoveFollow", "K2Node_BreakStruct_1", "S_WallHandFollow"),
]


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


# 1) 리컴파일 → 콜노드 핀 재구성
run("bp-compile1", *bp("compile_blueprint", asset_path=BP), 120)
g = dump()
cfg = next(n for n in g["nodes"] if n["class"] == "K2Node_CallFunction"
           and any(p["name"] == "RWall" for p in n["pins"]))
CFG = cfg["id"]
CX, CY = cfg["pos"]
print(f"== GetConfig 콜노드: {CFG} ==")
existing = {p["name"]: (p.get("connected_to") or []) for p in cfg["pins"]}


def need(pin, target):
    return not any(target in c for c in existing.get(pin, []))


if need("execute", "K2Node_FunctionEntry_0"):
    con("exec", "K2Node_FunctionEntry_0", "then", CFG, "execute")
if need("then", "K2Node_VariableSet_0"):
    con("then", CFG, "then", "K2Node_VariableSet_0", "execute")
if need("self", "K2Node_VariableGet_4"):
    con("self", "K2Node_VariableGet_4", "WallHandConfig", CFG, "self")
for sp, tn, tp in KEEP:
    if need(sp, tn):
        con(f"rw-{sp}", CFG, sp, tn, tp)

# 2) BreakStruct ×3 + 연결
BR = {}
for i, (name, st) in enumerate((("RWall", SIDE), ("LWall", SIDE), ("FWall", FRONT))):
    BR[name] = add(f"br-{name}", node_type="BreakStruct", struct_type=st,
                   position=[CX + 260, CY + 640 + i * 260])
    con(f"cfg→{name}", CFG, name, BR[name], st.split(".")[-1])

# 3) 맹글링 멤버 핀 해석
g = dump()
member = {}  # member[(wall, field)] = mangled pin name
for name in BR:
    n = next(x for x in g["nodes"] if x["id"] == BR[name])
    for p in n["pins"]:
        if p["direction"] == "output":
            base = p["name"].split("_")[0]
            member[(name, base)] = p["name"]
print("멤버 핀:", {k: v[:18] for k, v in list(member.items())[:6]}, "...")

# 4) BreakV2D ×9
BV = {}
v2d_members = [("RWall", "HandOffset"), ("RWall", "JogOffset"), ("RWall", "RunOffset"), ("RWall", "SprintOffset"),
               ("LWall", "HandOffset"), ("LWall", "JogOffset"), ("LWall", "RunOffset"), ("LWall", "SprintOffset"),
               ("FWall", "HandOffset")]
for i, (w, f) in enumerate(v2d_members):
    BV[(w, f)] = add(f"bv-{w}.{f}", node_type="CallFunction", function_name="BreakVector2D",
                     position=[CX + 560, CY + 640 + i * 90])
    con(f"{w}.{f}→bv", BR[w], member[(w, f)], BV[(w, f)], "InVec")

# 5) 속도별 전방 X: SelectFloat A←R.X (+), 기존 neg 노드 A←L.X (−)
con("fwdJ-R", BV[("RWall", "JogOffset")], "X", "K2Node_CallFunction_1", "A")
con("fwdJ-L", BV[("LWall", "JogOffset")], "X", "K2Node_CallFunction_65", "A")
con("fwdR-R", BV[("RWall", "RunOffset")], "X", "K2Node_CallFunction_30", "A")
con("fwdR-L", BV[("LWall", "RunOffset")], "X", "K2Node_CallFunction_76", "A")
con("fwdS-R", BV[("RWall", "SprintOffset")], "X", "K2Node_CallFunction_64", "A")
con("fwdS-L", BV[("LWall", "SprintOffset")], "X", "K2Node_CallFunction_92", "A")

# 6) 속도별 높이 Y: Run/Sprint 기존 SelectFloat A/B 교체, Jog 신규 SelectFloat
con("hR-R", BV[("RWall", "RunOffset")], "Y", "K2Node_CallFunction_32", "A")
con("hR-L", BV[("LWall", "RunOffset")], "Y", "K2Node_CallFunction_32", "B")
con("hS-R", BV[("RWall", "SprintOffset")], "Y", "K2Node_CallFunction_31", "A")
con("hS-L", BV[("LWall", "SprintOffset")], "Y", "K2Node_CallFunction_31", "B")
SFJY = add("sfjy", node_type="CallFunction", function_name="SelectFloat", position=[CX + 820, CY + 700])
con("hJ-R", BV[("RWall", "JogOffset")], "Y", SFJY, "A")
con("hJ-L", BV[("LWall", "JogOffset")], "Y", SFJY, "B")
con("hJ-b", "K2Node_Knot_15", "OutputPin", SFJY, "bPickA")
con("hJ→sel", SFJY, "ReturnValue", "K2Node_Select_2", "SBWalk_Jogging")

# 7) 정적 손 오프셋: X(앞뒤) 기존 SFX/NEG 입력 교체, Y(위) 신규 — 분기 전 스플라이스 (좌손 버그 수정)
con("hx-R", BV[("RWall", "HandOffset")], "X", "K2Node_CallFunction_99", "A")
con("hx-L", BV[("LWall", "HandOffset")], "X", "K2Node_CallFunction_98", "A")
SUY = add("suy", node_type="CallFunction", function_name="SelectFloat", position=[CX + 820, CY + 820])
con("hy-R", BV[("RWall", "HandOffset")], "Y", SUY, "A")
con("hy-L", BV[("LWall", "HandOffset")], "Y", SUY, "B")
con("hy-b", "K2Node_Knot_15", "OutputPin", SUY, "bPickA")
MKZ = add("mkz", node_type="CallFunction", function_name="MakeVector", position=[CX + 980, CY + 820])
con("suy→mkz", SUY, "ReturnValue", MKZ, "Z")
ADDV = add("addv", node_type="CallFunction", function_name="Add_VectorVector", position=[CX + 1140, CY + 820])
con("cf90→addv", "K2Node_CallFunction_90", "ReturnValue", ADDV, "A")
con("mkz→addv", MKZ, "ReturnValue", ADDV, "B")
con("addv→knot34", ADDV, "ReturnValue", "K2Node_Knot_34", "InputPin")

# 8) 구 우손 전용 Y 경로 차단 (CF_119.A 입력 절단 → 디폴트 0)
run("cut-oldY", *bp("disconnect_pins", asset_path=BP, graph_name=G,
                    source_node="K2Node_Knot_108", source_pin="OutputPin",
                    target_node="K2Node_CallFunction_119", target_pin="A"), 80)
# 구 RightHandOffset Break(CF_97) 제거 (소스 필드 소멸)
run("rm-cf97", *bp("remove_node", asset_path=BP, graph_name=G, node_id="K2Node_CallFunction_97"), 80)

# 9) IKStrength 모드 선택: (R/L by bRight) → (F by bFront) → Knot_2
SIK1 = add("sik1", node_type="CallFunction", function_name="SelectFloat", position=[CX + 820, CY + 940])
con("ik-R", BR["RWall"], member[("RWall", "IKStrength")], SIK1, "A")
con("ik-L", BR["LWall"], member[("LWall", "IKStrength")], SIK1, "B")
con("ik-b", "K2Node_Knot_15", "OutputPin", SIK1, "bPickA")
SIK2 = add("sik2", node_type="CallFunction", function_name="SelectFloat", position=[CX + 980, CY + 940])
con("ik-F", BR["FWall"], member[("FWall", "IKStrength")], SIK2, "A")
con("ik-side", SIK1, "ReturnValue", SIK2, "B")
con("ik-bf", "K2Node_Knot_80", "OutputPin", SIK2, "bPickA")
con("ik→knot2", SIK2, "ReturnValue", "K2Node_Knot_2", "InputPin")

# 10) 거리 모드 선택 ×2 → Knot_77/79
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

# 11) 정면 손: FWall.HandOffset → 기존 CF_96 Break
con("fw→cf96", BV[("FWall", "HandOffset")], "X", "K2Node_Knot_92", "InputPin")
con("fw→cf96b", BV[("FWall", "HandOffset")], "X", "K2Node_Knot_93", "InputPin")
con("fw→cf96c", BV[("FWall", "HandOffset")], "Y", "K2Node_Knot_74", "InputPin")
con("fw→cf96d", BV[("FWall", "HandOffset")], "Y", "K2Node_Knot_90", "InputPin")
run("rm-cf96", *bp("remove_node", asset_path=BP, graph_name=G, node_id="K2Node_CallFunction_96"), 80)

run("bp-compile2", *bp("compile_blueprint", asset_path=BP), 300)

# 12) 최종 스캔
g = dump()
cfg = next(n for n in g["nodes"] if n["id"] == CFG)
bad = [p["name"] for p in cfg["pins"] if p["direction"] == "output"
       and p["name"] != "then" and not p.get("connected_to")]
print("미연결 출력:", bad if bad else "없음")
# 핵심 Select 입력 무결성
for nid in ("K2Node_CallFunction_1", "K2Node_CallFunction_30", "K2Node_CallFunction_64",
            "K2Node_CallFunction_32", "K2Node_CallFunction_31", "K2Node_CallFunction_99",
            "K2Node_CallFunction_98", SFJY, SUY, SIK1, SIK2):
    n = next(x for x in g["nodes"] if x["id"] == nid)
    holes = [p["name"] for p in n["pins"] if p["direction"] == "input"
             and p["name"] in ("A", "B", "bPickA") and not p.get("connected_to")]
    if holes:
        print(f"!! {nid} 미연결 입력: {holes}")
print("== Script B done ==")
