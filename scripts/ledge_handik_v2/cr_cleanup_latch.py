import unreal, json
OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/cr_cleanup.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
log = {"removed": [], "skipped": []}
try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
    g = c.get_graph()
    DEAD = ["LatchToWorldL", "LatchToWorldR", "LatchInvM2W", "LatchInvM2W_1",
            "LatchToCompL", "LatchToCompR", "LatchLessL", "LatchLessR",
            "LatchSelL", "LatchSelR", "HandZBiasL", "HandZBiasR",
            "VariableNode_5", "VariableNode_6", "VariableNode_7", "VariableNode_8",
            "VariableNode_9", "VariableNode_10", "VariableNode_11", "VariableNode_12",
            "RerouteNode_12", "RerouteNode_13"]
    for name in DEAD:
        n = g.find_node_by_name(name)
        if n is None:
            log["skipped"].append(name + ":not_found")
            continue
        ok = c.remove_node_by_name(name, True)
        (log["removed"] if ok else log["skipped"]).append(name)
    # 삭제 후 완전 고아가 된 리루트만 추가 제거 (사용자 레이아웃 리루트는 링크가 남아 보존됨)
    for n in list(g.get_nodes()):
        path = n.get_node_path()
        if not path.startswith("RerouteNode"):
            continue
        linked = False
        for p in n.get_pins():
            if p.get_linked_source_pins() or p.get_linked_target_pins():
                linked = True
                break
        if not linked:
            ok = c.remove_node_by_name(path, True)
            if ok:
                log["removed"].append(path + " (고아 리루트)")
    bp.recompile_vm()
    saved = unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False)
    log["saved"] = bool(saved)
except Exception:
    import traceback
    log["error"] = traceback.format_exc()
with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1)
