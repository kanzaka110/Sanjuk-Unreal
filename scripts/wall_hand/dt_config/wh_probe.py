# -*- coding: utf-8 -*-
"""PIE 라이브 프로브: 벽손 알파 파이프라인 수치 로깅 (slate post-tick 상주).
로그: C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/wh_probe.csv"""
import unreal

OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/wh_probe.csv"
state = {"t": 0.0, "n": 0}
open(OUT, "w", encoding="utf-8").write(
    "n,alphaTarget,wallHandAlpha,whAlphaScaled,whBlendT_bp,turnBlockT,dtRowOK\n")

def find_pawn():
    for w in unreal.EditorLevelLibrary.get_game_worlds() if hasattr(unreal.EditorLevelLibrary, "get_game_worlds") else []:
        pass
    try:
        pcs = unreal.GameplayStatics.get_all_actors_of_class(
            unreal.EditorLevelLibrary.get_game_world() if hasattr(unreal.EditorLevelLibrary, "get_game_world") else None, None)
    except Exception:
        pass
    return None

def tick(dt):
    state["t"] += dt
    if state["t"] < 0.15:
        return
    state["t"] = 0.0
    try:
        world = None
        try:
            world = unreal.UnrealEditorSubsystem and unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        except Exception:
            pass
        if not world:
            return
        pawn = unreal.GameplayStatics.get_player_pawn(world, 0)
        if not pawn or "PC_01" not in pawn.get_name():
            return
        mesh = pawn.get_editor_property("Mesh")
        abp = mesh.get_anim_instance() if mesh else None
        if not abp:
            return
        def gv(o, n):
            try:
                return float(o.get_editor_property(n))
            except Exception:
                return float("nan")
        at = gv(abp, "WallHandAlphaTarget")
        al = gv(abp, "WallHandAlpha")
        sc = gv(abp, "WHAlphaScaled")
        tb = gv(abp, "WHTurnBlockT")
        bt = gv(pawn, "WHBlendT")
        try:
            dtb = pawn.get_editor_property("WallHandConfigTable")
            ok = 1 if dtb else 0
        except Exception:
            ok = -1
        state["n"] += 1
        with open(OUT, "a", encoding="utf-8") as f:
            f.write(f"{state['n']},{at:.3f},{al:.3f},{sc:.3f},{bt:.3f},{tb:.3f},{ok}\n")
    except Exception:
        pass

h = unreal.register_slate_post_tick_callback(tick)
print("WH_PROBE armed:", h)
