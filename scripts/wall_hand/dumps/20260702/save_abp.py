import unreal
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/save_result.txt"
bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP")
ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
open(OUT, "w").write(f"save_packages={ok}")
