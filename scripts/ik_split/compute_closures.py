# -*- coding: utf-8 -*-
"""섹션별 EventGraph 노드 클로저 계산 (exec 멤버 + 데이터 입력 조상). 드라이런 — 출력만."""
import json, io, os, collections
HERE = os.path.dirname(os.path.abspath(__file__))
inner = json.loads(json.loads(io.open(os.path.join(HERE, "layer_EventGraph.json"), encoding="utf-8").read())["result"]["content"][0]["text"])
nodes = {n["id"]: n for n in inner["nodes"]}

def data_ancestors(nid, seen):
    """입력 데이터 핀의 소스 노드 재귀 수집 (exec 제외)."""
    n = nodes[nid]
    for p in n.get("pins") or []:
        if p.get("type") == "exec" or p["direction"] != "input":
            continue
        for t in p.get("connected_to") or []:
            src = t.rsplit(".", 1)[0]
            if src in nodes and src not in seen:
                seen.add(src)
                data_ancestors(src, seen)

# 섹션별 exec 멤버 (분석 출력 기반 명시)
SEC_EXEC = {
 "WallHand": ["K2Node_CallFunction_14","K2Node_VariableSet_5","K2Node_VariableSet_6","K2Node_VariableSet_7","K2Node_VariableSet_8","K2Node_VariableSet_9","K2Node_VariableSet_10","K2Node_VariableSet_12","K2Node_VariableSet_11","K2Node_VariableSet_13"],
 "Ledge": ["K2Node_CallFunction_33","K2Node_CallFunction_34","K2Node_VariableSet_26","K2Node_VariableSet_16","K2Node_VariableSet_17","K2Node_VariableSet_18","K2Node_VariableSet_19","K2Node_VariableSet_20","K2Node_VariableSet_21","K2Node_VariableSet_22","K2Node_VariableSet_23","K2Node_VariableSet_24","K2Node_VariableSet_25","K2Node_VariableSet_29","K2Node_VariableSet_40","K2Node_VariableSet_41","K2Node_ExecutionSequence_1","K2Node_Knot_5","K2Node_IfThenElse_3","K2Node_IfThenElse_1","K2Node_IfThenElse_4","K2Node_CallFunction_60","K2Node_VariableSet_27","K2Node_CallFunction_18","K2Node_CallFunction_58","K2Node_Knot_12","K2Node_IfThenElse_5","K2Node_IfThenElse_6","K2Node_CallFunction_19","K2Node_CallFunction_21"],
 "WallRun": ["K2Node_CallFunction_7"],
 "Ladder": ["K2Node_Knot_4","K2Node_CallFunction_30","K2Node_VariableSet_31","K2Node_VariableSet_32","K2Node_VariableSet_33","K2Node_VariableSet_34","K2Node_VariableSet_35","K2Node_VariableSet_36","K2Node_VariableSet_37","K2Node_VariableSet_38","K2Node_CallFunction_11","K2Node_CallFunction_12","K2Node_CallFunction_4","K2Node_CallFunction_1"],
}
COMMON = ["K2Node_Event_1","K2Node_DynamicCast_1","K2Node_VariableSet_4","K2Node_DynamicCast_2","K2Node_VariableSet_15","K2Node_DynamicCast_0","K2Node_VariableSet_28","K2Node_SwitchEnum_0","K2Node_VariableSet_30"]

all_claimed = set()
for name, ids in list(SEC_EXEC.items()) + [("COMMON", COMMON)]:
    closure = set(ids)
    for nid in ids:
        data_ancestors(nid, closure)
    print(f"### {name}: {len(closure)} nodes")
    for nid in sorted(closure):
        n = nodes[nid]
        tag = "" if nid in ids else "  (data)"
        print(f"   {n['class'].replace('K2Node_',''):24s} {n['title'].splitlines()[0][:70]} [{nid}]{tag}")
    all_claimed |= closure
    print()

rest = [n for nid, n in nodes.items() if nid not in all_claimed]
print(f"### 잔존(바디) 후보: {len(rest)} nodes")
for n in rest:
    print(f"   {n['class'].replace('K2Node_',''):24s} {n['title'].splitlines()[0][:70]} [{n['id']}]")
