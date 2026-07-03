import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/flip_result.txt"
L=[]
try:
    # 1) CR: SideRotL Roll -60 → +60 (좌손 미러 — 실측 palmDotL -1.00 flush가 +60 방향)
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    val = "(Rotation=(X=0.500000,Y=0.000000,Z=0.000000,W=0.866025),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))"
    ok = ctrl.set_pin_default_value("SideRotL.OffsetTransform", val)
    L.append(f"SideRotL Roll +60 -> {ok}")
    bp.recompile_vm(); bp.recompile_vm_if_required()
    ok2 = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"CR save={ok2}")
    # 2) ABP: RunDeg -60 → 24
    cls = unreal.load_object(None, "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP.PC_01_ABP_C")
    cdo = unreal.get_default_object(cls)
    cdo.set_editor_property("WHSideRotRunDeg", 24.0)
    abp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP")
    unreal.BlueprintEditorLibrary.compile_blueprint(abp)
    ok3 = unreal.EditorLoadingAndSavingUtils.save_packages([abp.get_package()], False)
    L.append(f"RunDeg=24, ABP save={ok3}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
