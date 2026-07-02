import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/enum_probe2.txt"
L = []
try:
    cls = unreal.load_object(None, "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP.PC_01_ABP_C")
    cdo = unreal.get_default_object(cls)
    e = type(cdo.get_editor_property("StateMachineMoveState"))
    L.append(f"enum class: {e}")
    for name in dir(e):
        if name.startswith("_"): continue
        try:
            m = getattr(e, name)
            if isinstance(m, e): L.append(f"  {name} = {m.value}")
        except Exception: pass
    try:
        se = unreal.find_object(None, "/Script/SB2.SBStateMachineState")
        L.append(f"find_object: {se}")
        if se:
            n = se.get_editor_property("names") if hasattr(se,"get_editor_property") else None
    except Exception as ex:
        L.append("find ERR " + str(ex)[:100])
except Exception:
    L.append(traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(L))
