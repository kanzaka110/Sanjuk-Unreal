# PIE 라이브 PC_01 CMC MaxDepenetrationWithPawn 런타임 변경 (에셋 무변경, 단일 변수 실험)
import unreal

OUT = r"C:/Dev/Sanjuk-Unreal/Saved/cmc_set_result.txt"
NEW_VALUE = 2.0
lines = []
try:
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Character) if world else []
    for a in actors:
        if not a.get_name().startswith("PC_01"):
            continue
        cmc = a.get_editor_property("CharacterMovement")
        before = cmc.get_editor_property("MaxDepenetrationWithPawn")
        cmc.set_editor_property("MaxDepenetrationWithPawn", NEW_VALUE)
        after = cmc.get_editor_property("MaxDepenetrationWithPawn")
        lines.append("%s MaxDepenetrationWithPawn: %s -> %s" % (a.get_name(), before, after))
    if not lines:
        lines.append("NO_PC01_IN_PIE")
except Exception as e:
    lines.append("TOP_ERR: %s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("[CMC_SET] " + " | ".join(lines))
