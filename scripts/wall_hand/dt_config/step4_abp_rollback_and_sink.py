# -*- coding: utf-8 -*-
"""Step4: (a) alpha 함수에서 DT/커브 노드 롤백 — 엔게이지/벽yaw만 유지, alpha 계산은 BP로 이관.
(b) ABP에 BP→ABP 값 주입용 SetWallHandBlend 함수 신설 (게임스레드 전용, 스레드세이프 아님).
(c) GetWallHandState에 TurnBlockT 출력 추가 (BP가 턴타이머 읽는 용도)."""
from mono import bp
import json, sys

ABP = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
GA = "SetSmoothedWallHandAlpha"

def run(tag, err, out, n=160):
    print(f"[{tag}]", "ERR" if err else "OK", out[:n])
    if err:
        sys.exit(f"STOP at {tag}")
    return out

# ── (a) 롤백: 신규 15노드 + VS_0(Set WallHandAlpha) + alpha 잔존 노드 제거
# 먼저 exec 복구: Entry → VS_1(WHEngageR)
run("exec-fix", *bp("connect_pins", asset_path=ABP, graph_name=GA,
                    source_node="K2Node_FunctionEntry_0", source_pin="then",
                    target_node="K2Node_VariableSet_1", target_pin="execute"))
for nid in ["K2Node_CallFunction_17", "K2Node_BreakStruct_0",
            "K2Node_VariableSet_3", "K2Node_VariableSet_4", "K2Node_VariableSet_6",
            "K2Node_VariableSet_7", "K2Node_VariableGet_0", "K2Node_VariableGet_5",
            "K2Node_CallFunction_19", "K2Node_CallFunction_20", "K2Node_CallFunction_21",
            "K2Node_CallFunction_26", "K2Node_CallFunction_27", "K2Node_CallFunction_28",
            "K2Node_CallFunction_29",
            "K2Node_VariableSet_0",  # Set WallHandAlpha (BP가 직접 주입)
            "K2Node_CallFunction_1", "K2Node_CallFunction_6", "K2Node_CallFunction_7",
            "K2Node_CallFunction_8", "K2Node_Knot_1",
            "K2Node_VariableGet_16", "K2Node_VariableGet_1", "K2Node_VariableGet_2",
            "K2Node_VariableGet_3", "K2Node_VariableGet_4"]:
    err, out = bp("remove_node", asset_path=ABP, graph_name=GA, node_id=nid)
    print(f"[rm {nid}]", "ERR" if err else "OK", out[:90])

# ── (b) SetWallHandBlend 함수 신설
run("addfn", *bp("add_function", asset_path=ABP, function_name="SetWallHandBlend",
                 inputs=[{"name": "InAlpha", "type": "float"},
                         {"name": "InAlphaScaled", "type": "float"},
                         {"name": "InApproachDist", "type": "float"},
                         {"name": "InTurnBlockHold", "type": "float"}]))
GB = "SetWallHandBlend"
ids = {}
for i, var in enumerate(["WallHandAlpha", "WHAlphaScaled", "WHApproachDist", "WHTurnBlockHold"]):
    out = run(f"set-{var}", *bp("add_node", asset_path=ABP, graph_name=GB,
                                node_type="VariableSet", variable_name=var,
                                position=[300 + i * 250, 0]))
    ids[var] = json.loads(out)["id"]

# entry 핀 이름 확인
out = run("entry", *bp("get_graph_data", asset_path=ABP, graph_name=GB), 0)
g = json.loads(out)
entry = next(n for n in g["nodes"] if n["class"] == "K2Node_FunctionEntry")
print("entry pins:", [p["name"] for p in entry["pins"]])

def con(tag, sn, sp, tn, tp):
    run(tag, *bp("connect_pins", asset_path=ABP, graph_name=GB,
                 source_node=sn, source_pin=sp, target_node=tn, target_pin=tp))

E = entry["id"]
con("e→s1", E, "then", ids["WallHandAlpha"], "execute")
con("s1→s2", ids["WallHandAlpha"], "then", ids["WHAlphaScaled"], "execute")
con("s2→s3", ids["WHAlphaScaled"], "then", ids["WHApproachDist"], "execute")
con("s3→s4", ids["WHApproachDist"], "then", ids["WHTurnBlockHold"], "execute")
con("a→v1", E, "InAlpha", ids["WallHandAlpha"], "WallHandAlpha")
con("a→v2", E, "InAlphaScaled", ids["WHAlphaScaled"], "WHAlphaScaled")
con("a→v3", E, "InApproachDist", ids["WHApproachDist"], "WHApproachDist")
con("a→v4", E, "InTurnBlockHold", ids["WHTurnBlockHold"], "WHTurnBlockHold")

# ── (c) GetWallHandState 출력 TurnBlockT 추가 + 배선
run("fn-out", *bp("set_function_params", asset_path=ABP, function_name="GetWallHandState",
                  outputs=[{"name": "TurnBlockT", "type": "float"}]))
out = run("vg-tbt", *bp("add_node", asset_path=ABP, graph_name="GetWallHandState",
                        node_type="VariableGet", variable_name="WHTurnBlockT", position=[-300, 300]))
vg = json.loads(out)["id"]
run("tbt→ret", *bp("connect_pins", asset_path=ABP, graph_name="GetWallHandState",
                   source_node=vg, source_pin="WHTurnBlockT",
                   target_node="K2Node_FunctionResult_0", target_pin="TurnBlockT"))

# ── 컴파일
run("compile", *bp("compile_blueprint", asset_path=ABP), 500)
print("== step4 done ==")
