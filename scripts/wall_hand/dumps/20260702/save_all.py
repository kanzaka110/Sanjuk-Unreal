import unreal
pk=[]
for p in ("/Game/Art/Character/PC/PC_01/Blueprint/PC_01_BP",
          "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP",
          "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK"):
    pk.append(unreal.load_asset(p).get_package())
ok = unreal.EditorLoadingAndSavingUtils.save_packages(pk, False)
open(r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/save_result.txt","w").write(f"save_all={ok}")
