# -*- coding: utf-8 -*-
"""벽별 분리 최종: 잔여 글로벌 8필드(AttachSpeed/ReleaseSpeed/TurnReleaseSpeed/SpineLeanMaxDeg/
TurnBlockHold/ElbowAngleDeg/IdleFollow/MoveFollow) 전부 벽 구조체로 흡수.
UDS 멤버 추가 API 없음 → 테어다운(BS 제거→PDA 비우기→UDS 삭제) 후 풀 재생성.
최종: PDA 3필드(RWall/LWall/FWall), Side 15멤버 / Front 12멤버."""
from mono import bp
import json, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

DIR = "/Game/Art/Character/PC/PC_01/Blueprint/WallHandIK"
PDA = f"{DIR}/PDA_WallHandIKConfig"
BPP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP"
G = "UpdateWallHandIK"
SIDE = f"{DIR}/S_WallHandSideConfig"
FRONT = f"{DIR}/S_WallHandFrontConfig"
FOLLOW = f"{DIR}/S_WallHandFollow.S_WallHandFollow"

COMMON = [
    {"name": "IKStrength", "type": "float", "default_value": "1.0"},
    {"name": "AttachStartDist", "type": "float", "default_value": "60.0"},
    {"name": "AttachFullDist", "type": "float", "default_value": "45.0"},
    {"name": "AttachSpeed", "type": "struct:Vector2D", "default_value": "(X=1.0,Y=12.0)"},
    {"name": "ReleaseSpeed", "type": "struct:Vector2D", "default_value": "(X=4.5,Y=8.0)"},
    {"name": "TurnReleaseSpeed", "type": "float", "default_value": "28.0"},
    {"name": "SpineLeanMaxDeg", "type": "float", "default_value": "28.6"},
    {"name": "TurnBlockHold", "type": "float", "default_value": "0.8"},
    {"name": "ElbowAngleDeg", "type": "float", "default_value": "1.1"},
    {"name": "IdleFollow", "type": f"struct:{FOLLOW}"},
    {"name": "MoveFollow", "type": f"struct:{FOLLOW}"},
]
SIDE_FIELDS = COMMON[:3] + [
    {"name": "HandOffset", "type": "struct:Vector2D", "default_value": "(X=0.0,Y=0.0)"},
    {"name": "JogOffset", "type": "struct:Vector2D", "default_value": "(X=5.0,Y=0.0)"},
    {"name": "RunOffset", "type": "struct:Vector2D", "default_value": "(X=20.0,Y=-5.0)"},
    {"name": "SprintOffset", "type": "struct:Vector2D", "default_value": "(X=60.0,Y=-10.0)"},
] + COMMON[3:]
FRONT_FIELDS = COMMON[:3] + [
    {"name": "HandOffset", "type": "struct:Vector2D", "default_value": "(X=12.4,Y=12.4)"},
] + COMMON[3:]

PDA_REMOVE = ["RWall", "LWall", "FWall", "AttachSpeed", "ReleaseSpeed", "TurnReleaseSpeed",
              "SpineLeanMaxDeg", "ElbowAngleDeg", "TurnBlockHold", "IdleFollow", "MoveFollow"]

K15, K80 = "K2Node_Knot_15", "K2Node_Knot_80"  # bRight / bFront


def run(tag, err, out, n=90):
    print(f"[{tag}]", "ERR" if err else "OK", out[:n])
    if err:
        sys.exit(f"STOP {tag}")
    return out


def soft(tag, err, out, n=70):
    print(f"[{tag}]", "ERR" if err else "OK", out[:n])


def con(tag, sn, sp, tn, tp):
    run(tag, *bp("connect_pins", asset_path=BPP, graph_name=G,
                 source_node=sn, source_pin=sp, target_node=tn, target_pin=tp), 40)


def add(tag, **kw):
    return json.loads(run(tag, *bp("add_node", asset_path=BPP, graph_name=G, **kw), 40))["id"]


def dump():
    err, out = bp("get_graph_data", asset_path=BPP, graph_name=G)
    assert not err, out[:200]
    return json.loads(out)


# ── T1: BP BreakStruct 5개 제거 ──
for bs in ("K2Node_BreakStruct_0", "K2Node_BreakStruct_1", "K2Node_BreakStruct_2",
           "K2Node_BreakStruct_3", "K2Node_BreakStruct_4"):
    soft(f"rm-{bs[-13:]}", *bp("remove_node", asset_path=BPP, graph_name=G, node_id=bs))

# ── T2: PDA 비우기 ──
run("fn-del", *bp("remove_function", asset_path=PDA, name="GetConfig"))
for v in PDA_REMOVE:
    soft(f"del-{v}", *bp("remove_variable", asset_path=PDA, name=v))
run("pda-compile-empty", *bp("compile_blueprint", asset_path=PDA), 120)

# ── T3: UDS 삭제 ──
err, out = bp("delete_assets", asset_paths=[SIDE, FRONT])
if err:
    err, out = bp("delete_assets", paths=[SIDE, FRONT])
run("uds-del", err, out, 150)

# ── T4: UDS 재생성 (풀 멤버) ──
run("uds-side", *bp("create_user_defined_struct", save_path=SIDE, fields=SIDE_FIELDS), 90)
run("uds-front", *bp("create_user_defined_struct", save_path=FRONT, fields=FRONT_FIELDS), 90)

# ── T5: PDA 재구성 ──
run("add-RWall", *bp("add_variable", asset_path=PDA, name="RWall", type=f"struct:{SIDE}.S_WallHandSideConfig"))
run("add-LWall", *bp("add_variable", asset_path=PDA, name="LWall", type=f"struct:{SIDE}.S_WallHandSideConfig"))
run("add-FWall", *bp("add_variable", asset_path=PDA, name="FWall", type=f"struct:{FRONT}.S_WallHandFrontConfig"))
run("fn-add", *bp("add_function", asset_path=PDA, name="GetConfig"))
OUTS = [("RWall", f"struct:{SIDE}.S_WallHandSideConfig"), ("LWall", f"struct:{SIDE}.S_WallHandSideConfig"),
        ("FWall", f"struct:{FRONT}.S_WallHandFrontConfig")]
run("fn-outs", *bp("set_function_params", asset_path=PDA, function_name="GetConfig",
                   outputs=[{"name": n, "type": t} for n, t in OUTS]))
out = run("fn-graph", *bp("get_graph_data", asset_path=PDA, graph_name="GetConfig"), 0)
gg = json.loads(out)
entry = next(n["id"] for n in gg["nodes"] if n["class"] == "K2Node_FunctionEntry")
result = next(n["id"] for n in gg["nodes"] if n["class"] == "K2Node_FunctionResult")
run("e→r", *bp("connect_pins", asset_path=PDA, graph_name="GetConfig",
               source_node=entry, source_pin="then", target_node=result, target_pin="execute"))
for i, (n, t) in enumerate(OUTS):
    o = run(f"get-{n}", *bp("add_node", asset_path=PDA, graph_name="GetConfig",
                            node_type="VariableGet", variable_name=n, position=[-400, i * 100]), 40)
    run(f"wire-{n}", *bp("connect_pins", asset_path=PDA, graph_name="GetConfig",
                         source_node=json.loads(o)["id"], source_pin=n, target_node=result, target_pin=n), 40)
run("pda-compile", *bp("compile_blueprint", asset_path=PDA), 200)

# ── T6: BP 재배선 ──
run("bp-compile1", *bp("compile_blueprint", asset_path=BPP), 120)
g = dump()
cfg = next(n for n in g["nodes"] if n["class"] == "K2Node_CallFunction"
           and any(p["name"] == "RWall" for p in n["pins"]))
CFG = cfg["id"]
CX, CY = cfg["pos"]
print(f"== GetConfig 콜노드: {CFG} ==")
ex = {p["name"]: (p.get("connected_to") or []) for p in cfg["pins"]}
if not any("K2Node_FunctionEntry_0" in c for c in ex.get("execute", [])):
    con("exec", "K2Node_FunctionEntry_0", "then", CFG, "execute")
if not any("K2Node_VariableSet_0" in c for c in ex.get("then", [])):
    con("then", CFG, "then", "K2Node_VariableSet_0", "execute")
if not any("K2Node_VariableGet_4" in c for c in ex.get("self", [])):
    con("self", "K2Node_VariableGet_4", "WallHandConfig", CFG, "self")

BR = {}
for i, (name, st) in enumerate((("RWall", f"{SIDE}.S_WallHandSideConfig"),
                                ("LWall", f"{SIDE}.S_WallHandSideConfig"),
                                ("FWall", f"{FRONT}.S_WallHandFrontConfig"))):
    BR[name] = add(f"br-{name}", node_type="BreakStruct", struct_type=st,
                   position=[CX + 260, CY + 640 + i * 420])
    con(f"cfg→{name}", CFG, name, BR[name], st.split(".")[-1])

g = dump()
member = {}
for name in BR:
    n = next(x for x in g["nodes"] if x["id"] == BR[name])
    for p in n["pins"]:
        if p["direction"] == "output":
            member[(name, p["name"].split("_")[0])] = p["name"]

# 기존 BV/셀렉트 재연결 (1차 분리분)
REWIRE_BV = [("RWall", "HandOffset", "K2Node_CallFunction_103"), ("RWall", "JogOffset", "K2Node_CallFunction_104"),
             ("RWall", "RunOffset", "K2Node_CallFunction_106"), ("RWall", "SprintOffset", "K2Node_CallFunction_114"),
             ("LWall", "HandOffset", "K2Node_CallFunction_115"), ("LWall", "JogOffset", "K2Node_CallFunction_116"),
             ("LWall", "RunOffset", "K2Node_CallFunction_123"), ("LWall", "SprintOffset", "K2Node_CallFunction_124"),
             ("FWall", "HandOffset", "K2Node_CallFunction_125")]
for w, f, bv in REWIRE_BV:
    con(f"bv-{w[0]}{f[:4]}", BR[w], member[(w, f)], bv, "InVec")
REWIRE_SEL = [("RWall", "IKStrength", "K2Node_CallFunction_130", "A"), ("LWall", "IKStrength", "K2Node_CallFunction_130", "B"),
              ("FWall", "IKStrength", "K2Node_CallFunction_131", "A"),
              ("RWall", "AttachStartDist", "K2Node_CallFunction_132", "A"), ("LWall", "AttachStartDist", "K2Node_CallFunction_132", "B"),
              ("FWall", "AttachStartDist", "K2Node_CallFunction_133", "A"),
              ("RWall", "AttachFullDist", "K2Node_CallFunction_134", "A"), ("LWall", "AttachFullDist", "K2Node_CallFunction_134", "B"),
              ("FWall", "AttachFullDist", "K2Node_CallFunction_135", "A")]
for w, f, tn, tp in REWIRE_SEL:
    con(f"sel-{w[0]}{f[:4]}", BR[w], member[(w, f)], tn, tp)


def tree2(tag, fld, comp, tgt_node, tgt_pin, yoff, kind="SelectFloat", srcpins=None):
    """R/L→bRight, F/측면→bFront 2단 셀렉트. comp=None이면 BS 멤버 직접, 아니면 BV[wall].comp"""
    S1 = add(f"{tag}1", node_type="CallFunction", function_name=kind, position=[CX + 1350, CY + yoff])
    S2 = add(f"{tag}2", node_type="CallFunction", function_name=kind, position=[CX + 1510, CY + yoff])
    if srcpins:
        con(f"{tag}-R", srcpins["R"][0], srcpins["R"][1], S1, "A")
        con(f"{tag}-L", srcpins["L"][0], srcpins["L"][1], S1, "B")
        con(f"{tag}-F", srcpins["F"][0], srcpins["F"][1], S2, "A")
    else:
        con(f"{tag}-R", BR["RWall"], member[("RWall", fld)], S1, "A")
        con(f"{tag}-L", BR["LWall"], member[("LWall", fld)], S1, "B")
        con(f"{tag}-F", BR["FWall"], member[("FWall", fld)], S2, "A")
    con(f"{tag}-b", K15, "OutputPin", S1, "bPickA")
    con(f"{tag}-side", S1, "ReturnValue", S2, "B")
    con(f"{tag}-bf", K80, "OutputPin", S2, "bPickA")
    con(f"{tag}→", S2, "ReturnValue", tgt_node, tgt_pin)
    return S2


# 스칼라 4종 (float 2단 트리 → 실소비처)
tree2("tr", "TurnReleaseSpeed", None, "K2Node_CallFunction_95", "InWHTurnRelSpd", 0)
tree2("tb", "TurnBlockHold", None, "K2Node_CallFunction_95", "InWHTurnBlockHold", 120)
tree2("sl", "SpineLeanMaxDeg", None, "K2Node_CallFunction_120", "A", 240)
tree2("el", "ElbowAngleDeg", None, "K2Node_CallFunction_122", "A", 360)

# V2D 2종 (벽별 BreakV2D → 성분별 트리 → CF_95)
for tag, fld, pinX, pinY, yb in (("as", "AttachSpeed", "InWHAttachSpdStart", "InWHAttachSpdEnd", 500),
                                 ("rs", "ReleaseSpeed", "InWHRelSpdSlow", "InWHRelSpdFast", 760)):
    BV = {}
    for j, w in enumerate(("RWall", "LWall", "FWall")):
        BV[w] = add(f"{tag}bv-{w[0]}", node_type="CallFunction", function_name="BreakVector2D",
                    position=[CX + 1180, CY + yb + j * 80])
        con(f"{tag}bv-{w[0]}c", BR[w], member[(w, fld)], BV[w], "InVec")
    tree2(f"{tag}x", None, None, "K2Node_CallFunction_95", pinX, yb,
          srcpins={"R": (BV["RWall"], "X"), "L": (BV["LWall"], "X"), "F": (BV["FWall"], "X")})
    tree2(f"{tag}y", None, None, "K2Node_CallFunction_95", pinY, yb + 130,
          srcpins={"R": (BV["RWall"], "Y"), "L": (BV["LWall"], "Y"), "F": (BV["FWall"], "Y")})

# 구 글로벌 V2D Break 제거
soft("rm-cf102", *bp("remove_node", asset_path=BPP, graph_name=G, node_id="K2Node_CallFunction_102"))
soft("rm-cf105", *bp("remove_node", asset_path=BPP, graph_name=G, node_id="K2Node_CallFunction_105"))

# Follow: 벽별 Idle/Move → BreakStruct(S_WallHandFollow) ×6 → Pct/Bone 트리
FB = {}
for j, (w, st8) in enumerate([(w, s) for w in ("RWall", "LWall", "FWall") for s in ("IdleFollow", "MoveFollow")]):
    FB[(w, st8)] = add(f"fb-{w[0]}{st8[:4]}", node_type="BreakStruct", struct_type=FOLLOW,
                       position=[CX + 1180, CY + 1040 + j * 90])
    con(f"fb-{w[0]}{st8[:4]}c", BR[w], member[(w, st8)], FB[(w, st8)], "S_WallHandFollow")
g = dump()
fmem = {}
for key, nid in FB.items():
    n = next(x for x in g["nodes"] if x["id"] == nid)
    for p in n["pins"]:
        if p["direction"] == "output":
            fmem[key + (p["name"].split("_")[0],)] = p["name"]

# Pct 트리: idle → CF_108.B / move → CF_108.A
tree2("pi", None, None, "K2Node_CallFunction_108", "B", 1600,
      srcpins={w[0].upper() if False else k: v for k, v in {}.items()} or
      {"R": (FB[("RWall", "IdleFollow")], fmem[("RWall", "IdleFollow", "Pct")]),
       "L": (FB[("LWall", "IdleFollow")], fmem[("LWall", "IdleFollow", "Pct")]),
       "F": (FB[("FWall", "IdleFollow")], fmem[("FWall", "IdleFollow", "Pct")])})
tree2("pm", None, None, "K2Node_CallFunction_108", "A", 1720,
      srcpins={"R": (FB[("RWall", "MoveFollow")], fmem[("RWall", "MoveFollow", "Pct")]),
               "L": (FB[("LWall", "MoveFollow")], fmem[("LWall", "MoveFollow", "Pct")]),
               "F": (FB[("FWall", "MoveFollow")], fmem[("FWall", "MoveFollow", "Pct")])})
# Bone 트리 (SelectName): idle → CF_109 / move → CF_110
tree2("ni", None, None, "K2Node_CallFunction_109", "InSocketName", 1840, kind="SelectName",
      srcpins={"R": (FB[("RWall", "IdleFollow")], fmem[("RWall", "IdleFollow", "Bone")]),
               "L": (FB[("LWall", "IdleFollow")], fmem[("LWall", "IdleFollow", "Bone")]),
               "F": (FB[("FWall", "IdleFollow")], fmem[("FWall", "IdleFollow", "Bone")])})
tree2("nm", None, None, "K2Node_CallFunction_110", "InSocketName", 1960, kind="SelectName",
      srcpins={"R": (FB[("RWall", "MoveFollow")], fmem[("RWall", "MoveFollow", "Bone")]),
               "L": (FB[("LWall", "MoveFollow")], fmem[("LWall", "MoveFollow", "Bone")]),
               "F": (FB[("FWall", "MoveFollow")], fmem[("FWall", "MoveFollow", "Bone")])})

run("bp-compile2", *bp("compile_blueprint", asset_path=BPP), 300)

# 최종 스캔
g = dump()
cfg = next(n for n in g["nodes"] if n["id"] == CFG)
bad = [p["name"] for p in cfg["pins"] if p["direction"] == "output"
       and p["name"] != "then" and not p.get("connected_to")]
print("GetConfig 미연결 출력:", bad if bad else "없음")
holes_any = False
for n in g["nodes"]:
    if n["class"] == "K2Node_CallFunction" and any(
            k in str(n.get("title", "")) for k in ("Select Float", "Select Name")):
        holes = [p["name"] for p in n["pins"] if p["direction"] == "input"
                 and p["name"] in ("A", "B", "bPickA") and not p.get("connected_to")]
        if holes:
            print(f"!! {n['id']} [{str(n['title'])[:20]}] 미연결: {holes}")
            holes_any = True
if not holes_any:
    print("셀렉트 입력: 전부 연결")
print("== wall_split_full done ==")
