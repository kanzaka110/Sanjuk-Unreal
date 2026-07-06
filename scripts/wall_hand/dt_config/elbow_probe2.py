# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/elbow_probe2.txt"
state = {"t": 0.0}
def tick(dt):
    state["t"] += dt
    if state["t"] < 0.5:
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
        mesh = pawn.get_editor_property("Mesh")
        abp = mesh.get_anim_instance()
        rows.append(f"ABP.WHElbowRad = {abp.get_editor_property('WHElbowRad'):.4f}")
        try:
            insts = mesh.get_linked_anim_instances()
            for inst in (insts or []):
                nm = inst.get_class().get_name()
                try:
                    v = inst.get_editor_property("WHElbowRad")
                    rows.append(f"LAYER {nm}.WHElbowRad = {v:.4f}")
                except Exception:
                    pass
                try:
                    r = inst.get_editor_property("WHReleased")
                    rows.append(f"LAYER {nm}.WHReleased = {r}")
                except Exception:
                    pass
        except Exception as e:
            rows.append(f"linked FAIL {str(e)[:70]}")
        open(OUT, "w", encoding="utf-8").write("\n".join(rows))
    except Exception:
        open(OUT, "w", encoding="utf-8").write("FATAL\n" + traceback.format_exc())
h = unreal.register_slate_post_tick_callback(tick)
