# -*- coding: utf-8 -*-
"""섹션별 업데이트 로직/변수를 서브 ABP로 이관하는 드라이버.
사용: py migrate_updates.py <phase>   (vars | wallrun | wallhand | ladder | ledge | verify)
"""
import json, subprocess, io, os, sys, collections
MCP = "http://localhost:9316/mcp"
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "/Game/Art/Character/PC/PC_01/Blueprint/"
LAY = BASE + "PC_01_AnimLayer_IK"
ABP = {"WallHand": BASE + "WallHandIK/PC_01_AnimLayer_WallHandIK", "Ledge": BASE + "CustomMove_Ledge/PC_01_AnimLayer_Ledge",
       "WallRun": BASE + "CustomMove_WallRun/PC_01_AnimLayer_WallRun", "Ladder": BASE + "CustomMove_Ladder/PC_01_AnimLayer_Ladder"}
LGRAPH = {"WallHand": "WallHandIK", "Ledge": "Ledge", "WallRun": "WallRun", "Ladder": "Ladder"}

def call(action, args, tool="blueprint_query"):
    p = {"jsonrpc":"2.0","method":"tools/call","id":1,
         "params":{"name":tool,"arguments":{"action":action,"params":args} if tool!="blueprint_query" else {"action":action, **args}}}
    r = subprocess.run(["curl","-s","-X","POST",MCP,"-H","Content-Type: application/json","-d",json.dumps(p)],
                       capture_output=True, text=True, timeout=120)
    try:
        res = json.loads(r.stdout)["result"]
        txt = res["content"][0]["text"]
        ok = not res.get("isError")
        return ok, txt
    except Exception as e:
        return False, r.stdout[:400]

def must(action, args, tool="blueprint_query", note=""):
    ok, txt = call(action, args, tool)
    tag = "OK " if ok else "FAIL"
    print(f"[{tag}] {action} {note} :: {txt[:160]}")
    if not ok:
        print("  !! args:", json.dumps(args, ensure_ascii=False)[:300])
    return ok, txt

V = "struct:Vector"; F = "float"; B = "bool"
COMMON_VARS = [("As SBCharacter","object:SBCharacter","Reference"),
               ("As SBCharacterABP","object:PC_01_ABP_C","Reference"),
               ("SBCharacterMovementComponent","object:SBCharacterMovementComponent","Reference"),
               ("CustomMoveState","byte","디폴트")]
SEC_VARS = {
 "WallHand": [("WallHandTarget",V),("WallHandAlpha",F),("bWallHandRight",B),("WallHandSpineLean",F),
              ("bWallHandFront",B),("WallHandTargetL",V),("WHFrontBlend",F),("WHReleased",B),("WHElbowRad",F)],
 "Ledge": [("LedgeDangleAlpha",F),("LedgePelvisSpring",F),("LedgeHandIKAlphaL",F),("LedgeHandIKAlphaR",F),
           ("LedgeHandWorldPredL",V),("LedgeHandWorldPredR",V),("LedgeFootIdleCompL",V),("LedgeFootIdleCompR",V),
           ("LedgeFootIKAlphaL",F),("LedgeFootIKAlphaR",F),("LedgeSlopeDzBody",F),
           ("LedgePhysProfileOn",B),("LedgePhysWanted",B),("LedgePhysAnimAlpha",F)],
 "WallRun": [("WRIKMasterAlpha",F),("WRIKPlanePointCS",V),("WRIKNormalCS",V),("WallRunIKWallDist",F)],
 "Ladder": [("LadderHandTargetL",V),("LadderHandTargetR",V),("LadderFootTargetL",V),("LadderFootTargetR",V),
            ("LadderHandAlphaL",F),("LadderHandAlphaR",F),("LadderFootAlphaL",F),("LadderFootAlphaR",F)],
}
CAT = {"WallHand": "Wall Hand IK", "Ledge": "Custom Move Ledge", "WallRun": "WallRun IK", "Ladder": "Ladder IK"}

# EventGraph 클로저 (compute_closures.py 출력 기반)
COMMON_EG = ["K2Node_Event_1","K2Node_DynamicCast_1","K2Node_VariableSet_4","K2Node_DynamicCast_2","K2Node_VariableSet_15",
             "K2Node_DynamicCast_0","K2Node_VariableSet_28","K2Node_SwitchEnum_0","K2Node_VariableSet_30",
             "K2Node_CallFunction_0","K2Node_CallFunction_41","K2Node_CallFunction_5","K2Node_CallFunction_6",
             "K2Node_CastByteToEnum_0","K2Node_VariableGet_10","K2Node_VariableGet_2","K2Node_VariableGet_24","K2Node_VariableGet_8"]
EG = {
 "WallHand": ["K2Node_CallFunction_14","K2Node_CallFunction_20","K2Node_CallFunction_23","K2Node_CallFunction_8",
              "K2Node_Knot_13","K2Node_Knot_14","K2Node_Knot_15","K2Node_Knot_16","K2Node_Knot_17","K2Node_Knot_18",
              "K2Node_Knot_19","K2Node_Knot_9","K2Node_VariableGet_12","K2Node_VariableSet_10","K2Node_VariableSet_11",
              "K2Node_VariableSet_12","K2Node_VariableSet_13","K2Node_VariableSet_5","K2Node_VariableSet_6",
              "K2Node_VariableSet_7","K2Node_VariableSet_8","K2Node_VariableSet_9"],
 "Ledge": ["K2Node_CallFunction_10","K2Node_CallFunction_13","K2Node_CallFunction_15","K2Node_CallFunction_16",
           "K2Node_CallFunction_18","K2Node_CallFunction_19","K2Node_CallFunction_21","K2Node_CallFunction_22",
           "K2Node_CallFunction_24","K2Node_CallFunction_25","K2Node_CallFunction_26","K2Node_CallFunction_27",
           "K2Node_CallFunction_29","K2Node_CallFunction_31","K2Node_CallFunction_33","K2Node_CallFunction_34",
           "K2Node_CallFunction_58","K2Node_CallFunction_60","K2Node_ExecutionSequence_1","K2Node_IfThenElse_1",
           "K2Node_IfThenElse_3","K2Node_IfThenElse_4","K2Node_IfThenElse_5","K2Node_IfThenElse_6",
           "K2Node_Knot_10","K2Node_Knot_11","K2Node_Knot_12","K2Node_Knot_22","K2Node_Knot_23","K2Node_Knot_24",
           "K2Node_Knot_25","K2Node_Knot_26","K2Node_Knot_27","K2Node_Knot_28","K2Node_Knot_29","K2Node_Knot_30",
           "K2Node_Knot_34","K2Node_Knot_35","K2Node_Knot_36","K2Node_Knot_5","K2Node_Knot_6","K2Node_Knot_7",
           "K2Node_VariableGet_11","K2Node_VariableGet_3","K2Node_VariableGet_4","K2Node_VariableGet_40",
           "K2Node_VariableGet_5","K2Node_VariableGet_6","K2Node_VariableGet_7","K2Node_VariableGet_9",
           "K2Node_VariableSet_16","K2Node_VariableSet_17","K2Node_VariableSet_18","K2Node_VariableSet_19",
           "K2Node_VariableSet_20","K2Node_VariableSet_21","K2Node_VariableSet_22","K2Node_VariableSet_23",
           "K2Node_VariableSet_24","K2Node_VariableSet_25","K2Node_VariableSet_26","K2Node_VariableSet_27",
           "K2Node_VariableSet_29","K2Node_VariableSet_40","K2Node_VariableSet_41","K2Node_ExecutionSequence_0"],
 "WallRun": ["K2Node_CallFunction_7"],
 "Ladder": ["K2Node_Knot_4","K2Node_CallFunction_30","K2Node_VariableSet_31","K2Node_VariableSet_32",
            "K2Node_VariableSet_33","K2Node_VariableSet_34","K2Node_VariableSet_35","K2Node_VariableSet_36",
            "K2Node_VariableSet_37","K2Node_VariableSet_38","K2Node_CallFunction_11","K2Node_CallFunction_12",
            "K2Node_CallFunction_4","K2Node_CallFunction_1","K2Node_VariableGet_19","K2Node_VariableGet_28",
            "K2Node_VariableGet_29","K2Node_VariableGet_30","K2Node_VariableGet_31"],
}
# 스파인 연결 (EventGraph): Update이벤트는 각 ABP 기존/신규 노드 사용
SPINE_ENTRY = {"WallHand": ("K2Node_SwitchEnum_0", "SB_MOVE_Slope", "K2Node_CallFunction_14", "execute"),
               "WallRun":  ("K2Node_SwitchEnum_0", "SB_MOVE_Slope", "K2Node_CallFunction_7", "execute"),
               "Ladder":   None,  # SB_MOVE_Ladder -> Knot_4 은 클로저 내부라 보존됨
               "Ledge":    None}  # SB_MOVE_Ledge -> CF_33 내부 보존

def phase_vars():
    for sec, abp in ABP.items():
        for name, t, cat in COMMON_VARS:
            must("add_variable", {"asset_path": abp, "name": name, "type": t, "category": cat,
                                  "instance_editable": False}, note=f"{sec}:{name}")
        for name, t in SEC_VARS[sec]:
            must("add_variable", {"asset_path": abp, "name": name, "type": t, "category": CAT[sec],
                                  "instance_editable": True}, note=f"{sec}:{name}")

def copy_eg(sec):
    abp = ABP[sec]
    ids = COMMON_EG + EG[sec]
    ok, txt = must("copy_nodes", {"source_asset": LAY, "source_graph": "EventGraph", "node_ids": ids,
                                  "target_asset": abp, "target_graph": "EventGraph"}, note=f"{sec} EG x{len(ids)}")
    return ok

def spine(sec):
    abp = ABP[sec]
    # Update 이벤트 찾기 (기본 스텁 존재 가정) -> 없으면 add_event_node
    ok, txt = call("get_graph_data", {"asset_path": abp, "graph_name": "EventGraph", "_fields": "nodes.id,nodes.class,nodes.title"})
    upd = None
    if ok:
        g = json.loads(txt)
        for n in g.get("nodes", []):
            if n["class"] == "K2Node_Event" and "Update Animation" in n["title"]:
                upd = n["id"]
    if not upd:
        ok, txt = must("add_event_node", {"asset_path": abp, "graph_name": "EventGraph",
                                          "event_name": "BlueprintUpdateAnimation"}, note=f"{sec} add update event")
        try: upd = json.loads(txt).get("node_id") or json.loads(txt).get("id")
        except Exception: pass
    print(f"  {sec} update event = {upd}")
    # CustomMoveState 변수 생략: CastByteToEnum → Switch.Selection 직결
    conns = [("K2Node_CastByteToEnum_0", "ReturnValue", "K2Node_SwitchEnum_0", "Selection")]
    if sec == "Ledge":
        conns.append((upd, "then", "K2Node_ExecutionSequence_0", "execute"))
    else:
        conns.append((upd, "then", "K2Node_SwitchEnum_0", "execute"))
    e = SPINE_ENTRY.get(sec)
    if e:
        conns.append(e)
    payload = [{"source_node": a, "source_pin": b, "target_node": c, "target_pin": d} for a, b, c, d in conns]
    must("connect_pins_bulk", {"asset_path": abp, "graph_name": "EventGraph", "connections": payload}, note=f"{sec} spine")
    # 잔재 정리: SetCustomMoveState/GetCustomMoveState 노드 + 변수 제거
    for nid in ("K2Node_VariableSet_30", "K2Node_VariableGet_2"):
        call("remove_node", {"asset_path": abp, "graph_name": "EventGraph", "node_id": nid})
    call("remove_variable", {"asset_path": abp, "name": "CustomMoveState"})

def fix_float_vars(sec):
    for name, t in SEC_VARS[sec]:
        if t == "float":
            must("set_variable_type", {"asset_path": ABP[sec], "name": name, "type": "double"}, note=f"{sec}:{name}->double")

def compile_save(asset):
    ok, txt = call("compile_blueprint", {"asset_path": asset, "_fields": "success,error_count,errors"})
    try:
        j = json.loads(txt)
        print(f"[COMPILE] {asset.rsplit('/',1)[1]} errors={j.get('error_count')} " +
              (json.dumps(j.get('errors'), ensure_ascii=False)[:400] if j.get('error_count') else ""))
    except Exception:
        print("[COMPILE?]", txt[:200])

# ---- 레이어 그래프 값 플러밍: ik_export.json 기반 클로저 계산 ----
def load_ik():
    return json.loads(json.loads(io.open(os.path.join(HERE, "ik_export.json"), encoding="utf-8").read())["result"]["content"][0]["text"])

def data_closure(nodes_by_id, seeds):
    seen = set(seeds)
    stack = list(seeds)
    while stack:
        nid = stack.pop()
        n = nodes_by_id.get(nid)
        if not n: continue
        for p in n.get("pins") or []:
            if p["direction"] != "input": continue
            for t in p.get("connected_to") or []:
                src = t.rsplit(".", 1)[0]
                if src in nodes_by_id and src not in seen and not src.startswith("AnimGraphNode"):
                    seen.add(src)
                    stack.append(src)
    return sorted(seen)

# (소스노드, 소스핀, 타깃노드, 타깃핀) — 서브 ABP 레이어 그래프 내 최종 연결
PLUMB = {
 "WallRun": {"seeds": ["K2Node_VariableGet_42","K2Node_VariableGet_40","K2Node_VariableGet_41"],
   "conns": [("K2Node_VariableGet_42","WRIKMasterAlpha","AnimGraphNode_ControlRig_8","Alpha"),
             ("K2Node_VariableGet_40","WRIKPlanePointCS","AnimGraphNode_ControlRig_8","WallPlanePoint"),
             ("K2Node_VariableGet_41","WRIKNormalCS","AnimGraphNode_ControlRig_8","WallNormal")]},
 "Ladder": {"seeds": ["K2Node_VariableGet_44","K2Node_VariableGet_45","K2Node_VariableGet_48","K2Node_VariableGet_49",
                      "K2Node_VariableGet_46","K2Node_VariableGet_47","K2Node_VariableGet_50","K2Node_VariableGet_51"],
   "conns": [("K2Node_VariableGet_44","LadderHandTargetL","AnimGraphNode_ControlRig_10","LadderHandTargetL"),
             ("K2Node_VariableGet_45","LadderHandTargetR","AnimGraphNode_ControlRig_10","LadderHandTargetR"),
             ("K2Node_VariableGet_48","LadderFootTargetL","AnimGraphNode_ControlRig_10","LadderFootTargetL"),
             ("K2Node_VariableGet_49","LadderFootTargetR","AnimGraphNode_ControlRig_10","LadderFootTargetR"),
             ("K2Node_VariableGet_46","LadderHandAlphaL","AnimGraphNode_ControlRig_10","LadderHandAlphaL"),
             ("K2Node_VariableGet_47","LadderHandAlphaR","AnimGraphNode_ControlRig_10","LadderHandAlphaR"),
             ("K2Node_VariableGet_50","LadderFootAlphaL","AnimGraphNode_ControlRig_10","LadderFootAlphaL"),
             ("K2Node_VariableGet_51","LadderFootAlphaR","AnimGraphNode_ControlRig_10","LadderFootAlphaR")]},
 "WallHand": {"seeds": ["K2Node_VariableGet_23","K2Node_VariableGet_11","K2Node_VariableGet_35","K2Node_VariableGet_27",
                        "K2Node_VariableGet_25","K2Node_VariableGet_29","K2Node_VariableGet_34","K2Node_VariableGet_33",
                        "K2Node_CallFunction_5","K2Node_CallFunction_6"],
   "conns": [("K2Node_VariableGet_23","WallHandAlpha","AnimGraphNode_ControlRig_4","Alpha"),
             ("K2Node_VariableGet_11","WHFrontBlend","AnimGraphNode_ControlRig_4","Weight"),
             ("K2Node_VariableGet_35","WallHandTarget","AnimGraphNode_ControlRig_4","LookAtLocation"),
             ("K2Node_VariableGet_27","bWallHandRight","AnimGraphNode_ControlRig_4","bWallHandRight"),
             ("K2Node_VariableGet_25","WallHandSpineLean","AnimGraphNode_ControlRig_4","WallHandSpineLean"),
             ("K2Node_VariableGet_29","bWallHandFront","AnimGraphNode_ControlRig_4","bWallHandFront"),
             ("K2Node_VariableGet_34","WallHandTargetL","AnimGraphNode_ControlRig_4","WallHandTargetL"),
             ("K2Node_VariableGet_33","WHElbowRad","AnimGraphNode_ControlRig_4","ElbowAngle"),
             ("K2Node_CallFunction_5","ReturnValue","AnimGraphNode_LayeredBoneBlend_0","BlendWeights_0"),
             ("K2Node_CallFunction_6","ReturnValue","AnimGraphNode_LayeredBoneBlend_0","BlendWeights_1")]},
 "Ledge": {"seeds": ["K2Node_CallFunction_1","K2Node_CallFunction_7","K2Node_VariableGet_12","K2Node_VariableGet_19",
                     "K2Node_VariableGet_7","K2Node_VariableGet_8","K2Node_VariableGet_13","K2Node_VariableGet_14",
                     "K2Node_VariableGet_15","K2Node_VariableGet_16","K2Node_VariableGet_4"],
   "conns": [("K2Node_CallFunction_1","ReturnValue","AnimGraphNode_ControlRig_11","Alpha"),
             ("K2Node_CallFunction_7","ReturnValue","AnimGraphNode_ControlRig_11","CharVelocity"),
             ("K2Node_VariableGet_12","LedgeHandWorldPredL","AnimGraphNode_ControlRig_11","HandTargetL"),
             ("K2Node_VariableGet_19","LedgeHandWorldPredR","AnimGraphNode_ControlRig_11","HandTargetR"),
             ("K2Node_VariableGet_7","LedgeHandIKAlphaL","AnimGraphNode_ControlRig_11","HandPinAlphaL"),
             ("K2Node_VariableGet_8","LedgeHandIKAlphaR","AnimGraphNode_ControlRig_11","HandPinAlphaR"),
             ("K2Node_VariableGet_13","LedgeFootIdleCompL","AnimGraphNode_ControlRig_11","FootTargetL"),
             ("K2Node_VariableGet_14","LedgeFootIdleCompR","AnimGraphNode_ControlRig_11","FootTargetR"),
             ("K2Node_VariableGet_15","LedgeFootIKAlphaL","AnimGraphNode_ControlRig_11","FootAlphaL"),
             ("K2Node_VariableGet_16","LedgeFootIKAlphaR","AnimGraphNode_ControlRig_11","FootAlphaR"),
             ("K2Node_VariableGet_4","LedgeSlopeDzBody","AnimGraphNode_ControlRig_11","PelvisSlopeLift")]},
}

WR_FUNC_NODES = ["K2Node_IfThenElse_0","K2Node_VariableSet_12","K2Node_VariableSet_13","K2Node_VariableSet_14",
                 "K2Node_VariableSet_15","K2Node_CallFunction_1","K2Node_CallFunction_2","K2Node_CallFunction_3",
                 "K2Node_CallFunction_42","K2Node_VariableGet_4","K2Node_VariableGet_1","K2Node_VariableGet_2",
                 "K2Node_BreakStruct_0","K2Node_Knot_7","K2Node_Knot_9","K2Node_Knot_0","K2Node_Knot_1"]

def wallrun_function():
    abp = ABP["WallRun"]
    must("add_function", {"asset_path": abp, "function_name": "UpdateWallRunLimbIK"}, note="WR func")
    must("copy_nodes", {"source_asset": LAY, "source_graph": "UpdateWallRunLimbIK", "node_ids": WR_FUNC_NODES,
                        "target_asset": abp, "target_graph": "UpdateWallRunLimbIK"}, note=f"WR func nodes x{len(WR_FUNC_NODES)}")
    # 엔트리 → 브랜치
    ok, txt = call("get_graph_data", {"asset_path": abp, "graph_name": "UpdateWallRunLimbIK", "_fields": "nodes.id,nodes.class"})
    entry = None
    for n in json.loads(txt).get("nodes", []):
        if n["class"] == "K2Node_FunctionEntry": entry = n["id"]
    must("connect_pins", {"asset_path": abp, "graph_name": "UpdateWallRunLimbIK",
                          "from_node": entry, "from_pin": "then", "to_node": "K2Node_IfThenElse_0", "to_pin": "execute"},
         note=f"WR entry({entry})")

def plumb(sec):
    abp, lg = ABP[sec], LGRAPH[sec]
    ik = load_ik()
    by_id = {n["id"]: n for n in ik["nodes"]}
    closure = data_closure(by_id, PLUMB[sec]["seeds"])
    must("copy_nodes", {"source_asset": LAY, "source_graph": "IK", "node_ids": closure,
                        "target_asset": abp, "target_graph": lg}, note=f"{sec} plumb x{len(closure)}")
    payload = [{"source_node": a, "source_pin": b, "target_node": c, "target_pin": d}
               for a, b, c, d in PLUMB[sec]["conns"]]
    must("connect_pins_bulk", {"asset_path": abp, "graph_name": lg, "connections": payload}, note=f"{sec} plumb conns")

MOVED_VARS = {
 "WallHand": [n for n, _ in SEC_VARS["WallHand"]],
 "Ledge": [n for n, _ in SEC_VARS["Ledge"]],
 "WallRun": [n for n, _ in SEC_VARS["WallRun"]],
 "Ladder": [n for n, _ in SEC_VARS["Ladder"]],
}

def cleanup():
    ik = load_ik()
    by_id = {n["id"]: n for n in ik["nodes"]}
    # 1) 레이어 노드 값핀 제거 (CustomPinProperties 비움 → reconstruct로 핀 소멸)
    for nid in ["AnimGraphNode_LinkedAnimLayer_1","AnimGraphNode_LinkedAnimLayer_4",
                "AnimGraphNode_LinkedAnimLayer_5","AnimGraphNode_LinkedAnimLayer_6"]:
        must("set_node_property", {"asset_path": LAY, "graph_name": "IK", "node_id": nid,
                                   "property_name": "CustomPinProperties", "value": "()"}, note=f"strip pins {nid}")
    # 2) IK 그래프 플러밍 노드 삭제
    for sec in PLUMB:
        for nid in data_closure(by_id, PLUMB[sec]["seeds"]):
            ok, txt = call("remove_node", {"asset_path": LAY, "graph_name": "IK", "node_id": nid})
            if not ok: print(f"[FAIL] rm IK {nid} :: {txt[:100]}")
    # 3) EventGraph 섹션 체인 삭제 (+SwitchEnum, Get CustomMoveState)
    eg_remove = set()
    for sec in EG:
        eg_remove |= set(EG[sec])
    eg_remove |= {"K2Node_SwitchEnum_0", "K2Node_VariableGet_2"}
    for nid in sorted(eg_remove):
        ok, txt = call("remove_node", {"asset_path": LAY, "graph_name": "EventGraph", "node_id": nid})
        if not ok: print(f"[FAIL] rm EG {nid} :: {txt[:100]}")
    # 4) UpdateWallRunLimbIK 함수 제거
    must("remove_function", {"asset_path": LAY, "name": "UpdateWallRunLimbIK"}, note="rm WR func")
    # 5) 이관 변수 제거
    for sec, names in MOVED_VARS.items():
        for name in names:
            ok, txt = call("remove_variable", {"asset_path": LAY, "name": name})
            if not ok: print(f"[FAIL] rm var {name} :: {txt[:100]}")
    compile_save(LAY)

def strip_interface():
    IFACE = BASE + "PC_01_AnimLayerInterface"
    for graph, nid in [("WallHandIK","AnimGraphNode_LinkedInputPose_4"),("Ledge","AnimGraphNode_LinkedInputPose_5"),
                       ("WallRun","AnimGraphNode_LinkedInputPose_6"),("Ladder","AnimGraphNode_LinkedInputPose_7")]:
        must("set_node_property", {"asset_path": IFACE, "graph_name": graph, "node_id": nid,
                                   "property_name": "Inputs", "value": "()"}, note=f"strip {graph} inputs")
    compile_save(IFACE)
    for sec in ABP:
        compile_save(ABP[sec])
    compile_save(LAY)
    compile_save(BASE + "PC_01_ABP")

if __name__ == "__main__":
    ph = sys.argv[1] if len(sys.argv) > 1 else ""
    if ph == "vars":
        phase_vars()
    elif ph in ("wallrun", "wallhand", "ladder", "ledge"):
        sec = {"wallrun":"WallRun","wallhand":"WallHand","ladder":"Ladder","ledge":"Ledge"}[ph]
        if sec == "WallRun":
            wallrun_function()
        fix_float_vars(sec)
        copy_eg(sec)
        spine(sec)
        plumb(sec)
        compile_save(ABP[sec])
    elif ph == "cleanup":
        cleanup()
    elif ph == "strip":
        strip_interface()
    else:
        print("phase: vars | wallrun | wallhand | ladder | ledge | cleanup | strip")
