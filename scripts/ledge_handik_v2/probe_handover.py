# 손 vs IK 타깃 동시 추적 v2 (에디터 py 전용)
import unreal, sys, time, types

for name in ("__ikv2__", "__ikdrift__", "__ikiso__", "__atprobe__", "__hover__"):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__hover__")
sys.modules["__hover__"] = mod
LOG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/handover.log"
open(LOG, "w").close()
NL = chr(10)
ANIMF = "Anim_3_CE8F6C8948855759C43A24A538203DDC"


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
        a = anim.get_editor_property("BlendStackInputs").get_editor_property(ANIMF)
        an = a.get_name() if a else "None"
        aL = float(anim.get_editor_property("LedgeHandIKAlphaL"))
        aR = float(anim.get_editor_property("LedgeHandIKAlphaR"))
        hl = mesh.get_socket_location("hand_l")
        hr = mesh.get_socket_location("hand_r")
        tl = anim.get_editor_property("LedgeHandDestL")
        tr_ = anim.get_editor_property("LedgeHandDestR")
        with open(LOG, "a") as f:
            f.write("t=%.3f mv=%d aL=%.2f aR=%.2f hL=(%.1f,%.1f,%.1f) tL=(%.1f,%.1f,%.1f) hR=(%.1f,%.1f,%.1f) tR=(%.1f,%.1f,%.1f) anim=%s%s"
                    % (time.time() - _st["t0"], mv, aL, aR,
                       hl.x, hl.y, hl.z, tl.x, tl.y, tl.z,
                       hr.x, hr.y, hr.z, tr_.x, tr_.y, tr_.z, an, NL))
    except Exception as e:
        with open(LOG, "a") as f:
            f.write("EXC %r%s" % (e, NL))
        try:
            unreal.unregister_slate_post_tick_callback(mod.handle)
        except Exception:
            pass
        mod.handle = None


mod.handle = unreal.register_slate_post_tick_callback(_tick)
print("HANDOVER_PROBE_V2_ON")
