import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/reset_result.txt"
L=[]
try:
    cls = unreal.load_object(None, "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP.PC_01_ABP_C")
    cdo = unreal.get_default_object(cls)
    for name, val in (("WHSideRotWalkDeg",12.0),("WHSideRotJogDeg",18.0),("WHSideRotRunDeg",24.0),("WHSideRotSprintDeg",30.0)):
        cur = cdo.get_editor_property(name)
        cdo.set_editor_property(name, val)
        L.append(f"{name}: {cur} -> {val}")
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"save={ok}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
