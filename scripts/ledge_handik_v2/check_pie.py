import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
unreal.log("PIE_RUNNING=" + str(w is not None))
