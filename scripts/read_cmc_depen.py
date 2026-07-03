# PIE 라이브 PC_01의 CMC 디페네트레이션 관련 현재값 읽기
import unreal

OUT = r"C:/Dev/Sanjuk-Unreal/Saved/cmc_depen_result.txt"
PROPS = [
    "MaxDepenetrationWithPawn",
    "MaxDepenetrationWithPawnAsProxy",
    "MaxDepenetrationWithGeometry",
    "MaxDepenetrationWithGeometryAsProxy",
    "bEnablePhysicsInteraction",
    "PushForceFactor",
    "InitialPushForceFactor",
    "MaxWalkSpeed",
]
lines = []
try:
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Character) if world else []
    for a in actors:
        n = a.get_name()
        if not (n.startswith("PC_01") or n.startswith("M_001")):
            continue
        cmc = a.get_editor_property("CharacterMovement")
        lines.append("%s cmc_class=%s" % (n, cmc.get_class().get_name() if cmc else None))
        for p in PROPS:
            try:
                lines.append("  %s = %s" % (p, cmc.get_editor_property(p)))
            except Exception as e:
                lines.append("  %s = ERR %s" % (p, e))
except Exception as e:
    lines.append("TOP_ERR: %s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("[CMC_DEPEN] " + " | ".join(lines))
