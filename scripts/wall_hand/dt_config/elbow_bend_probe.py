# -*- coding: utf-8 -*-
import unreal, traceback, math
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/elbow_bend.txt"
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
        mesh = pawn.get_editor_property("Mesh")
        rows = []
        for side in ("r", "l"):
            try:
                ua = mesh.get_socket_location(f"upperarm_{side}")
                la = mesh.get_socket_location(f"lowerarm_{side}")
                ha = mesh.get_socket_location(f"hand_{side}")
                v1 = (ua - la); v2 = (ha - la)
                v1n = v1.normal(); v2n = v2.normal()
                dot = max(-1.0, min(1.0, v1n.dot(v2n)))
                bend = 180.0 - math.degrees(math.acos(dot))
                rows.append(f"{side}: 팔꿈치굽음={bend:.1f}도 (0=완전펴짐)")
            except Exception as e:
                rows.append(f"{side} FAIL {str(e)[:50]}")
        open(OUT, "w", encoding="utf-8").write("\n".join(rows))
    except Exception:
        open(OUT, "w", encoding="utf-8").write("FATAL\n" + traceback.format_exc())
h = unreal.register_slate_post_tick_callback(tick)
