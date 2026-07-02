import unreal
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/enum_probe.txt"
L = []
try:
    cls = unreal.load_object(None, "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_ABP.PC_01_ABP_C")
    cdo = unreal.get_default_object(cls)
    for name in ("StateMachineMoveState", "MovementState", "AnimStance"):
        try:
            v = cdo.get_editor_property(name)
            L.append(f"{name}: value={v!r} type={type(v).__name__} typepath={type(v).__module__}.{type(v).__qualname__}")
        except Exception as e:
            L.append(f"{name}: ERR {str(e)[:120]}")
except Exception as e:
    L.append("ERR " + str(e)[:200])
open(OUT, "w", encoding="utf-8").write("\n".join(L))
unreal.log("[probe_enum] done")
