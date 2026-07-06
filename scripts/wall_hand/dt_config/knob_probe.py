# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/knob_probe.txt"
state = {"t": 0.0}
def tick(dt):
    state["t"] += dt
    if state["t"] < 0.4:
        return
    state["t"] = 0.0
    try:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if not world:
            return
        pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
        if not pawn or "PC_01" not in pawn.get_name():
            return
        rows = []
        cfg = pawn.get_editor_property("WallHandConfig")
        for p in ("RightHandHeight", "SpineLeanMaxDeg", "ElbowAngleDeg"):
            rows.append(f"cfg.{p} = {cfg.get_editor_property(p)}")
        mesh = pawn.get_editor_property("Mesh")
        abp = mesh.get_anim_instance()
        for v in ("WallHandAlpha", "WallHandSpineLean"):
            try:
                rows.append(f"ABP.{v} = {abp.get_editor_property(v):.3f}")
            except Exception:
                pass
        try:
            t = abp.get_editor_property("WallHandTargetWorld")
            rows.append(f"ABP.TargetWorld.Z = {t.z:.1f}")
        except Exception as e:
            rows.append(f"target FAIL {str(e)[:40]}")
        h = mesh.get_socket_location("hand_r")
        rows.append(f"hand_r.Z = {h.z:.1f}")
        open(OUT, "w", encoding="utf-8").write("\n".join(rows))
    except Exception:
        open(OUT, "w", encoding="utf-8").write("FATAL\n" + traceback.format_exc())
unreal.register_slate_post_tick_callback(tick)
