import unreal
bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK")
ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
open(r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/save_result.txt","w").write(f"layer save={ok}")
