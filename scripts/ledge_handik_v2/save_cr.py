import unreal
r1 = unreal.EditorAssetLibrary.save_asset("/Game/Art/Character/PC/PC_01/Blueprint/CustomMove_Ledge/PC_01_CtrlRig_LedgeDangle", only_if_is_dirty=False)
unreal.log("CR_SAVE=" + str(r1))
