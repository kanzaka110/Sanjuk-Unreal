import unreal
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/zero_result.txt"
cls = unreal.load_object(None, "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP.PC_01_ABP_C")
cdo = unreal.get_default_object(cls)
for n in ("WHSideRotWalkDeg","WHSideRotJogDeg","WHSideRotRunDeg","WHSideRotSprintDeg"):
    cdo.set_editor_property(n, 0.0)
bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP")
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
open(OUT,"w").write(f"all degs=0, save={ok}")
