import unreal
bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
bp.recompile_vm(); bp.recompile_vm_if_required()
ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
open(r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/save_result.txt","w").write(f"cr save={ok}")
