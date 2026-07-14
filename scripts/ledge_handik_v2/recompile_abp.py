import unreal
MOD = "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP"
bp = unreal.load_asset(MOD)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
r = unreal.EditorAssetLibrary.save_asset(MOD, only_if_is_dirty=False)
unreal.log("ABP_RECOMPILE_SAVE=" + str(r))
