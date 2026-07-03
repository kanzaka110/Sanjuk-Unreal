# PIE 런타임에서 PC_01 ABP 인스턴스의 AnimRewindRecording=True 켜기 (에셋 무변경)
import unreal

OUT = r"C:/Dev/Sanjuk-Unreal/Saved/abrr_toggle_result.txt"
lines = []
try:
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    if not world:
        lines.append("NO_PIE_WORLD")
    else:
        actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Character)
        lines.append("characters=%d" % len(actors))
        done = 0
        for a in actors:
            name = a.get_name()
            mesh = a.get_editor_property("mesh")
            if not mesh:
                continue
            ai = mesh.get_anim_instance()
            if not ai:
                continue
            cls = ai.get_class().get_name()
            if "PC_01_ABP" not in cls:
                lines.append("skip %s (%s)" % (name, cls))
                continue
            try:
                before = ai.get_editor_property("AnimRewindRecording")
            except Exception as e:
                before = "ERR:%s" % e
            try:
                ai.set_editor_property("AnimRewindRecording", True)
                after = ai.get_editor_property("AnimRewindRecording")
                done += 1
                lines.append("SET %s %s: %s -> %s" % (name, cls, before, after))
            except Exception as e:
                lines.append("FAIL %s %s: %s" % (name, cls, e))
        lines.append("done=%d" % done)
except Exception as e:
    lines.append("TOP_ERR: %s" % e)

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("[ABRR_TOGGLE] " + " | ".join(lines))

