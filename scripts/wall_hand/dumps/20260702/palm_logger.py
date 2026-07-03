# -*- coding: utf-8 -*-
"""손바닥 회전 정밀 측정 — palm축(+Y)·벽법선 dot + 모드/weight."""
import unreal, sys

OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/palm_log.csv"
ROWS = ["time,alpha,bF,bR,walkMode,sideRotW,palmDotR,palmDotL,fingDotR"]

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
        nm = g("WallHandNormal")
        qR = mesh.get_socket_quaternion("hand_r"); qL = mesh.get_socket_quaternion("hand_l")
        palmR = qR.rotate_vector(unreal.Vector(0,1,0))   # 손바닥-바깥 +Y (6/25 실측)
        palmL = qL.rotate_vector(unreal.Vector(0,-1,0))  # 미러
        fingR = qR.rotate_vector(unreal.Vector(-1,0,0))  # 손가락 -X
        def dot(a,b): return a.x*b.x + a.y*b.y + a.z*b.z
        n = unreal.Vector(nm.x,nm.y,nm.z)
        ROWS.append(f"{t:.3f},{al:.2f},{bf},{br},{wmv},{srw:.3f},{dot(palmR,n):.2f},{dot(palmL,n):.2f},{dot(fingR,n):.2f}")
        if len(ROWS)%120==0: _flush()
    except Exception:
        pass

def _flush():
    try: open(OUT,"w",encoding="utf-8").write("\n".join(ROWS))
    except Exception: pass

h = getattr(sys, "_WH_TURN_LOG_HANDLE", None)
if h:
    try: unreal.unregister_slate_post_tick_callback(h)
    except Exception: pass
sys._WH_TURN_LOG_HANDLE = unreal.register_slate_post_tick_callback(_tick)
unreal.log("[palm_logger] armed")
