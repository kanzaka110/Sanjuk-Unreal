import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/test_extreme_result.txt"
L = []
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    # 극단 테스트: 왼손 X축 -90도 (즉시 눈에 띔)
    val = "(Rotation=(X=-0.707107,Y=0.000000,Z=0.000000,W=0.707107),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))"
    ok = ctrl.set_pin_default_value("OffsetRotL.OffsetTransform", val)
    L.append(f"set extreme -90deg -> {ok}")
    bp.recompile_vm(); bp.recompile_vm_if_required()
    ok2 = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"save={ok2}")
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(L))
