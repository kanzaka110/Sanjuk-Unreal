import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/walkmode_probe.txt"
L=[]
try:
    cls = unreal.load_object(None, "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP.PC_01_ABP_C")
    cdo = unreal.get_default_object(cls)
    for prop in ("WalkMode","PendingWalkMode","CurrentWalkMode"):
        try:
            v = cdo.get_editor_property(prop)
            e = type(v)
            L.append(f"== {prop}: {e.__name__} = {v!r}")
            for name in dir(e):
                if name.startswith("_"): continue
                m = getattr(e, name)
                if isinstance(m, e): L.append(f"   {name} = {m.value}")
        except Exception as ex:
            L.append(f"== {prop} ERR {str(ex)[:80]}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
