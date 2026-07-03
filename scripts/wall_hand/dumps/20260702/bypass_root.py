import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/bypass_result.txt"
L=[]
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    # QMul 경유 제거: Effector.Rotation ← QSel 직결 (컴포넌트 공간 상수)
    for side in ("R","L"):
        ctrl.break_link(f"QMul{side}.Result", f"TwoBoneIK_{side}.Effector.Rotation")
        ctrl.add_link(f"QSel{side}.Result", f"TwoBoneIK_{side}.Effector.Rotation")
        L.append(f"{side}: Effector.Rotation ← QSel{side} 직결")
    bp.recompile_vm(); bp.recompile_vm_if_required()
    ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"save={ok}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
