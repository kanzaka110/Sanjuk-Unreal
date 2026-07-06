# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/root_axes.txt"
state = {"done": False, "t": 0.0}
def tick(dt):
    if state["done"]:
        return
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
        mesh = pawn.get_editor_property("Mesh")
        tf = mesh.get_socket_transform("root", unreal.RelativeTransformSpace.RTS_WORLD)
        q = tf.rotation
        x = q.rotate_vector(unreal.Vector(1, 0, 0))
        y = q.rotate_vector(unreal.Vector(0, 1, 0))
        z = q.rotate_vector(unreal.Vector(0, 0, 1))
        af = pawn.get_actor_forward_vector()
        ar = pawn.get_actor_right_vector()
        rows = [
            f"root X축 → world ({x.x:.2f},{x.y:.2f},{x.z:.2f})",
            f"root Y축 → world ({y.x:.2f},{y.y:.2f},{y.z:.2f})",
            f"root Z축 → world ({z.x:.2f},{z.y:.2f},{z.z:.2f})",
            f"액터 전방 ({af.x:.2f},{af.y:.2f},{af.z:.2f})",
            f"액터 우측 ({ar.x:.2f},{ar.y:.2f},{ar.z:.2f})",
        ]
        open(OUT, "w", encoding="utf-8").write("\n".join(rows))
        state["done"] = True
    except Exception:
        open(OUT, "w", encoding="utf-8").write("FATAL\n" + traceback.format_exc())
        state["done"] = True
unreal.register_slate_post_tick_callback(tick)
