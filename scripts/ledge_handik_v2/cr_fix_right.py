import unreal, json
OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/cr_fix_right.json"
CR = "/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle"
log = {}
try:
    bp = unreal.load_asset(CR)
    c = bp.get_controller_by_name("RigVMModel") or bp.get_controller()
    g = c.get_graph()
    # 회전 리루트 출처 기록 (검증용)
    for rn in ("RerouteNode_6", "RerouteNode_8"):
        n = g.find_node_by_name(rn)
        if n:
            p = n.find_pin("Value")
            log[rn + "_src"] = [s.get_pin_path() for s in p.get_linked_source_pins()]
    # 오른손 이펙터: Lerp_1 경유로 원복
    c.break_all_links("RigVMFunction_MathTransformMake_1.Translation", True)
    c.add_link("RigVMFunction_MathVectorLerp_1.Result",
               "RigVMFunction_MathTransformMake_1.Translation")
    log["right_effector"] = "Lerp_1.Result -> MakeTransform_1.Translation"
    bp.recompile_vm()
    saved = unreal.EditorAssetLibrary.save_asset(CR, only_if_is_dirty=False)
    log["saved"] = bool(saved)
except Exception:
    import traceback
    log["error"] = traceback.format_exc()
with open(OUT, "w") as fp:
    json.dump(log, fp, indent=1)
