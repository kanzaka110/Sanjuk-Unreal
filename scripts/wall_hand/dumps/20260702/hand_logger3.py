# -*- coding: utf-8 -*-
"""attach 오프셋 진단 로거 v3 — 양손 타겟의 벽법선 좌표 + engage/alpha/게이트 신호."""
import unreal, sys

OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/hand_log3.csv"
ROWS = ["time,alpha,aTgt,bR,bF,engR,engL,tR_n,tL_n,hR_n,hL_n,nx,ny"]

def _tick(dt):
    try:
        w = unreal.UnrealEditorSubsystem().get_game_world()
        if not w:
            if len(ROWS) > 1: _flush()
            return
        p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if not p: return
        mesh = p.get_component_by_class(unreal.SkeletalMeshComponent)
        ai = mesh.get_anim_instance() if mesh else None
        if not ai: return
        t = unreal.GameplayStatics.get_time_seconds(w)
        g = ai.get_editor_property
        al = float(g("WallHandAlpha")); at = float(g("WallHandAlphaTarget"))
        br = int(bool(g("bWallHandRight"))); bf = int(bool(g("bWallHandFront")))
        er = float(g("WHEngageR")); el = float(g("WHEngageL"))
        tw = g("WallHandTargetWorld"); tl = g("WallHandTargetL"); nm = g("WallHandNormal")
        hr = mesh.get_socket_location("hand_r"); hl = mesh.get_socket_location("hand_l")
        def dn(v): return v.x*nm.x + v.y*nm.y + v.z*nm.z  # 벽법선 축 좌표
        ROWS.append(f"{t:.3f},{al:.2f},{at:.2f},{br},{bf},{er:.2f},{el:.2f},"
                    f"{dn(tw):.1f},{dn(tl):.1f},{dn(hr):.1f},{dn(hl):.1f},{nm.x:.2f},{nm.y:.2f}")
        if len(ROWS) % 120 == 0: _flush()
    except Exception:
        pass

def _flush():
    try:
        with open(OUT, "w", encoding="utf-8") as f: f.write("\n".join(ROWS))
    except Exception: pass

h = getattr(sys, "_WH_TURN_LOG_HANDLE", None)
if h:
    try: unreal.unregister_slate_post_tick_callback(h)
    except Exception: pass
sys._WH_TURN_LOG_HANDLE = unreal.register_slate_post_tick_callback(_tick)
unreal.log("[hand_logger3] armed -> " + OUT)
