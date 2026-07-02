import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/fix_offsetrotl_result.txt"
L = []
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    val = "(Rotation=(X=-0.258819,Y=0.000000,Z=0.000000,W=0.965926),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))"
    ok = ctrl.set_pin_default_value("OffsetRotL.OffsetTransform", val)
    L.append(f"set OffsetTransform -> {ok}")
    g = ctrl.get_graph()
    for n in g.get_nodes():
        if n.get_name() == "OffsetRotL":
            for p in n.get_pins():
                if p.get_name() == "OffsetTransform":
                    L.append("now: " + p.get_default_value()[:130])
    bp.recompile_vm(); bp.recompile_vm_if_required()
    L.append("recompiled")
    ok2 = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"save_packages={ok2}")
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(L))
