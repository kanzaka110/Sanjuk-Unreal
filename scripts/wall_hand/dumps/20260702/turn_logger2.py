# -*- coding: utf-8 -*-
"""180도 턴 팔꼬임 진단 로거 — slate tick CSV.
TrjTurnAngle / Speed2D / WallHandAlpha(Target) / bWallHandRight / actor yaw 매 틱 기록.
시작: py 이 파일. 정지: PIE 종료(폰 소실 시 자동 flush) 또는 재실행(핸들 교체).
"""
import unreal, sys

OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/turn_log2.csv"
ROWS = ["time,turnAngle,speed2d,alpha,alphaTarget,bRight,actorYaw,smState,futSpd,futDot,blockT"]

def _find_pawn():
    try:
        w = unreal.UnrealEditorSubsystem().get_game_world()
        if not w: return None, None
        p = unreal.GameplayStatics.get_player_pawn(w, 0)
        if not p:
            actors = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Pawn)
            p = next((a for a in actors if "PC_01" in a.get_name()), None)
        return w, p
    except Exception:
        return None, None

def _flush():
    try:
        with open(OUT, "w", encoding="utf-8") as f:
            f.write("\n".join(ROWS))
    except Exception:
        pass

def _tick(dt):
    try:
        w, p = _find_pawn()
        if not p:
            if len(ROWS) > 1: _flush()
            return
        mesh = p.get_component_by_class(unreal.SkeletalMeshComponent)
        ai = mesh.get_anim_instance() if mesh else None
        if not ai: return
        t = unreal.GameplayStatics.get_time_seconds(w)
        ta = ai.get_editor_property("TrjTurnAngle")
        sp = ai.get_editor_property("Speed2D")
        al = ai.get_editor_property("WallHandAlpha")
        at = ai.get_editor_property("WallHandAlphaTarget")
        br = ai.get_editor_property("bWallHandRight")
        sm = ai.get_editor_property("StateMachineMoveState")
        yaw = p.get_actor_rotation().yaw
        fv = ai.get_editor_property("TrjFutureVelocity")
        nm = ai.get_editor_property("WallHandNormal")
        bt = ai.get_editor_property("WHTurnBlockT")
        import math
        fl = math.sqrt(fv.x*fv.x+fv.y*fv.y)
        fd = ((fv.x*nm.x+fv.y*nm.y+fv.z*nm.z)/fl) if fl>1 else 0.0
        ROWS.append(f"{t:.3f},{float(ta):.1f},{float(sp):.1f},{float(al):.3f},{float(at):.3f},{int(bool(br))},{yaw:.1f},{int(sm.value) if hasattr(sm,'value') else sm},{fl:.0f},{fd:.2f},{float(bt):.2f}")
        if len(ROWS) % 120 == 0: _flush()
    except Exception:
        pass

# 이전 핸들 제거 (reload 좀비 방지 — sys 저장 패턴)
h = getattr(sys, "_WH_TURN_LOG_HANDLE", None)
if h:
    try: unreal.unregister_slate_post_tick_callback(h)
    except Exception: pass
sys._WH_TURN_LOG_HANDLE = unreal.register_slate_post_tick_callback(_tick)
unreal.log("[turn_logger] armed -> " + OUT)
