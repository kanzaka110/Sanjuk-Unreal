import unreal

# PIE 중 핸드핀 IK 토글 — 실행할 때마다 on<->off
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
if w is None:
    unreal.log_warning("[HandIK] PIE not running")
else:
    pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
    mesh = pawn.get_components_by_class(unreal.SkeletalMeshComponent)[0]
    anim = mesh.get_anim_instance()
    cur = bool(anim.get_editor_property("bLedgeHandPinDisabled"))
    anim.set_editor_property("bLedgeHandPinDisabled", not cur)
    state = "OFF (disabled)" if not cur else "ON (enabled)"
    unreal.log("[HandIK] pin IK -> " + state)
