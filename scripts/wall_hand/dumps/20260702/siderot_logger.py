# -*- coding: utf-8 -*-
"""WHSideRotW 체인 진단 — ABP값 + hand_r 롤 변화."""
import unreal, sys

OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/siderot_log.csv"
ROWS = ["time,alpha,bF,bR,walkMode,sideRotW,handRollX"]

def _tick(dt):
    try:
        w = unreal.UnrealEditorSubsystem().get_game_world()
        if not w:
            if len(ROWS)>1: _flush()
            return
        p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if not p: return
        mesh = p.get_component_by_class(unreal.SkeletalMeshComponent)
        ai = mesh.get_anim_instance() if mesh else None
        if not ai: return
        g = ai.get_editor_property
        t = unreal.GameplayStatics.get_time_seconds(w)
        al = float(g("WallHandAlpha")); bf = int(bool(g("bWallHandFront"))); br = int(bool(g("bWallHandRight")))
        wm = g("PendingWalkMode"); wmv = int(wm.value) if hasattr(wm,"value") else wm
        srw = float(g("WHSideRotW"))
        q = mesh.get_socket_quaternion("hand_r")
        e = q.euler()
        ROWS.append(f"{t:.3f},{al:.2f},{bf},{br},{wmv},{srw:.3f},{e.x:.1f}")
        if len(ROWS)%120==0: _flush()
    except Exception:
        pass

def _flush():
    try:
        open(OUT,"w",encoding="utf-8").write("\n".join(ROWS))
    except Exception: pass

h = getattr(sys, "_WH_TURN_LOG_HANDLE", None)
if h:
    try: unreal.unregister_slate_post_tick_callback(h)
    except Exception: pass
sys._WH_TURN_LOG_HANDLE = unreal.register_slate_post_tick_callback(_tick)
unreal.log("[siderot_logger] armed")
