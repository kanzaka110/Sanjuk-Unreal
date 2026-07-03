import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/cr_wallyaw_result.txt"
L=[]
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    try: ctrl.break_link("DirYawR.Result", "DirQR.Angle")
    except Exception: pass
    ctrl.bind_pin_to_variable("DirQR.Angle", "Weight")
    try: ctrl.break_link("DirQL.Result", "QMulL.A")
    except Exception: pass
    ctrl.add_link("DirQR.Result", "QMulL.A")
    for nm in ("DirYawR","DirYawL","DirQL"):
        try: ctrl.remove_node_by_name(nm); L.append(f"remove {nm}")
        except Exception as e: L.append(f"remove {nm}: {str(e)[:50]}")
    bp.recompile_vm(); bp.recompile_vm_if_required()
    ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"save={ok}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
