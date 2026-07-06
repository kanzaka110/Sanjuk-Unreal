# -*- coding: utf-8 -*-
import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/elbow_probe3.txt"
LAYCLS = None
state = {"t": 0.0}
def tick(dt):
    global LAYCLS
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
        if LAYCLS is None:
            LAYCLS = unreal.load_object(None, "/Game/Art/Character/PC/PC_01/Blueprint/PC_01_AnimLayer_IK.PC_01_AnimLayer_IK_C")
        rows.append(f"laycls = {LAYCLS}")
        try:
            li = abp.get_linked_anim_layer_instance_by_class(LAYCLS)
            rows.append(f"layer inst = {li.get_name() if li else None}")
            if li:
                rows.append(f"LAYER.WHElbowRad = {li.get_editor_property('WHElbowRad'):.4f}")
        except Exception as e:
            rows.append(f"layer FAIL {str(e)[:80]}")
        open(OUT, "w", encoding="utf-8").write("\n".join(rows))
    except Exception:
        open(OUT, "w", encoding="utf-8").write("FATAL\n" + traceback.format_exc())
h = unreal.register_slate_post_tick_callback(tick)
