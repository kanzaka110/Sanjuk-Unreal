import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/cr_clean_result.txt"
L = []
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    for nm in ("VariableNode_5", "VariableNode_6"):
        ok = ctrl.remove_node_by_name(nm)
        L.append(f"remove {nm} -> {ok}")
    bp.recompile_vm(); bp.recompile_vm_if_required()
    ok2 = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"save={ok2}")
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(L))
