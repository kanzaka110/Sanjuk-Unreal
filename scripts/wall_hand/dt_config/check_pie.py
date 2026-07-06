# -*- coding: utf-8 -*-
import unreal
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/check_pie.txt"
pie = unreal.EditorLevelLibrary.get_editor_world().get_name() if hasattr(unreal,'EditorLevelLibrary') else '?'
sub = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = sub.get_editor_world()
res = [f"editor_world={w.get_name()}"]
try:
    res.append(f"pie_worlds={[x.get_name() for x in unreal.EditorLevelLibrary.get_all_level_actors()[:0]]}")
except Exception: pass
try:
    lp = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    res.append(f"is_in_pie={lp.is_in_play_in_editor()}")
except Exception as e:
    res.append(f"pie check fail {e}")
open(OUT,"w",encoding="utf-8").write("\n".join(res))
