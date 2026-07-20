# 골반 스프링 입력 실측 프로브 (에디터 py 전용)
# LedgeCalcVelocity 의 축별 성분 + pelvis_spring 커브값 + 실제 펠비스 월드좌표를 기록
# → 어느 축에 이동 성분이 실려 있는지 확정 (게인/마스크 축 배정 근거)
import unreal, sys, time, types

for name in ("__ikv2__", "__ikdrift__", "__hover__", "__bodyp__", "__over__", "__spring__"):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__spring__")
sys.modules["__spring__"] = mod
LOG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/spring_probe.log"
open(LOG, "w").close()
NL = chr(10)


def _tick(dt, _st={"t0": time.time()}):
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
        v = anim.get_editor_property("LedgeCalcVelocity")
        sp = float(anim.get_editor_property("LedgePelvisSpring"))
        pv = mesh.get_socket_location("pelvis")
        act = pawn.get_actor_location()
        fwd = pawn.get_actor_forward_vector()
        with open(LOG, "a") as f:
            f.write("t=%.3f vel=(%.1f,%.1f,%.1f) |v|=%.1f spring=%.2f pelvis=(%.1f,%.1f,%.1f) actor=(%.1f,%.1f,%.1f) fwd=(%.2f,%.2f,%.2f)%s"
                    % (time.time() - _st["t0"], v.x, v.y, v.z, v.length(), sp,
                       pv.x, pv.y, pv.z, act.x, act.y, act.z, fwd.x, fwd.y, fwd.z, NL))
    except Exception as e:
        with open(LOG, "a") as f:
            f.write("EXC %r%s" % (e, NL))
        try:
            unreal.unregister_slate_post_tick_callback(mod.handle)
        except Exception:
            pass
        mod.handle = None


mod.handle = unreal.register_slate_post_tick_callback(_tick)
print("SPRING_PROBE_ON")
