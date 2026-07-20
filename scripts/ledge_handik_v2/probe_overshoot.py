# 이동->Idle 전환 1틱 손 오버슈트 프로브 (에디터 py 전용, 매 틱)
# 손소켓 + Dest + WorldLatch + IdleComp + 커브/알파 + 애님명 동시 기록 -> overshoot.log
import unreal, sys, time, types

for name in ("__ikv2__", "__ikdrift__", "__ikiso__", "__atprobe__", "__hover__", "__bodyp__", "__over__"):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__over__")
sys.modules["__over__"] = mod
LOG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/overshoot.log"
open(LOG, "w").close()
NL = chr(10)
ANIMF = "Anim_3_CE8F6C8948855759C43A24A538203DDC"


def _v(o):
    return "(%.1f,%.1f,%.1f)" % (o.x, o.y, o.z)


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
        mv = int(bool(anim.get_editor_property("bTransitMoving")))
        a = anim.get_editor_property("BlendStackInputs").get_editor_property(ANIMF)
        an = a.get_name() if a else "None"
        aL = float(anim.get_editor_property("LedgeHandIKAlphaL"))
        aR = float(anim.get_editor_property("LedgeHandIKAlphaR"))
        cvL = float(anim.get_curve_value("ledge_hand_ik_l"))
        cvR = float(anim.get_curve_value("ledge_hand_ik_r"))
        hl = mesh.get_socket_location("hand_l")
        hr = mesh.get_socket_location("hand_r")
        dl = anim.get_editor_property("LedgeHandDestL")
        dr = anim.get_editor_property("LedgeHandDestR")
        wl = anim.get_editor_property("LedgeHandWorldL")
        wr = anim.get_editor_property("LedgeHandWorldR")
        with open(LOG, "a") as f:
            f.write("t=%.3f mv=%d aL=%.2f aR=%.2f cL=%.2f cR=%.2f hL=%s hR=%s dL=%s dR=%s wL=%s wR=%s anim=%s%s"
                    % (time.time() - _st["t0"], mv, aL, aR, cvL, cvR,
                       _v(hl), _v(hr), _v(dl), _v(dr), _v(wl), _v(wr), an, NL))
    except Exception as e:
        with open(LOG, "a") as f:
            f.write("EXC %r%s" % (e, NL))
        try:
            unreal.unregister_slate_post_tick_callback(mod.handle)
        except Exception:
            pass
        mod.handle = None


mod.handle = unreal.register_slate_post_tick_callback(_tick)
print("OVERSHOOT_PROBE_ON")
