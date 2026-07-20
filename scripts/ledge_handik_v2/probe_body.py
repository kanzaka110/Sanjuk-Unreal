# 몸 vs 팔 지연 분해 프로브 (에디터 py 전용)
# 손(hL/hR) + 액터캡슐(act) + 펠비스본(pv) + pelvis_spring 커브 + LedgePelvisSpring 동시 기록
# → 유닛무브 중 변위 도달 타이밍(손 vs 캡슐 vs 펠비스) 비교로 "몸 지연" 주범 분해
import unreal, sys, time, types

for name in ("__ikv2__", "__ikdrift__", "__ikiso__", "__atprobe__", "__hover__", "__bodyp__"):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__bodyp__")
sys.modules["__bodyp__"] = mod
LOG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/bodylag.log"
open(LOG, "w").close()
NL = chr(10)


def _tick(dt, _st={"t0": time.time(), "n": 0}):
    _st["n"] += 1
    if _st["n"] % 2 != 0:
        return
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None:
            return
        pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
        if pawn is None:
            return
        mesh = pawn.get_components_by_class(unreal.SkeletalMeshComponent)[0]
        anim = mesh.get_anim_instance()
        if anim is None:
            return
        lmd = anim.get_editor_property("LedgeMoveData")
        if not bool(lmd.get_editor_property("bActive")):
            return
        mv = int(bool(anim.get_editor_property("bTransitMoving")))
        act = pawn.get_actor_location()
        pv = mesh.get_socket_location("pelvis")
        hl = mesh.get_socket_location("hand_l")
        hr = mesh.get_socket_location("hand_r")
        aL = float(anim.get_editor_property("LedgeHandIKAlphaL"))
        aR = float(anim.get_editor_property("LedgeHandIKAlphaR"))
        try:
            ps = float(anim.get_curve_value("pelvis_spring"))
        except Exception:
            ps = -99.0
        try:
            sp = float(anim.get_editor_property("LedgePelvisSpring"))
        except Exception:
            sp = -99.0
        with open(LOG, "a") as f:
            f.write("t=%.3f mv=%d aL=%.2f aR=%.2f act=(%.1f,%.1f,%.1f) pv=(%.1f,%.1f,%.1f) hL=(%.1f,%.1f,%.1f) hR=(%.1f,%.1f,%.1f) ps=%.2f sp=%.2f%s"
                    % (time.time() - _st["t0"], mv, aL, aR,
                       act.x, act.y, act.z, pv.x, pv.y, pv.z,
                       hl.x, hl.y, hl.z, hr.x, hr.y, hr.z, ps, sp, NL))
    except Exception as e:
        with open(LOG, "a") as f:
            f.write("EXC %r%s" % (e, NL))
        try:
            unreal.unregister_slate_post_tick_callback(mod.handle)
        except Exception:
            pass
        mod.handle = None


mod.handle = unreal.register_slate_post_tick_callback(_tick)
print("BODYLAG_PROBE_ON")
