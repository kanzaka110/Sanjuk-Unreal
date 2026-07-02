import unreal
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/set_result.txt"
cls = unreal.load_object(None, "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP.PC_01_ABP_C")
cdo = unreal.get_default_object(cls)
cdo.set_editor_property("WHSideRotRunDeg", 24.0)
bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP")
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
open(OUT,"w").write(f"RunDeg=24, save={ok}")
