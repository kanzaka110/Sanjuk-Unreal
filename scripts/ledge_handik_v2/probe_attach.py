# 렛지 어태치 타이밍 프로브 — 상태 변화 프레임만 기록 (에디터 py 전용, HTTP 없음)
import unreal, sys, time, types

for name in ("__ikv2__", "__ikdrift__", "__ikiso__", "__atprobe__"):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__atprobe__")
sys.modules["__atprobe__"] = mod
LOG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/attach.log"
open(LOG, "w").close()
NL = chr(10)
ANIMF = "Anim_3_CE8F6C8948855759C43A24A538203DDC"


def _tick(dt, _st={"t0": time.time(), "n": 0, "prev": None}):
    _st["n"] += 1
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
        act = bool(lmd.get_editor_property("bActive"))
        mv = bool(anim.get_editor_property("bTransitMoving"))
        tr = bool(anim.get_editor_property("TransitingToNextLedge"))
        flag = bool(anim.get_editor_property("bLedgeEventAnim"))
        bsi = anim.get_editor_property("BlendStackInputs")
        a = bsi.get_editor_property(ANIMF)
        an = a.get_name() if a else "None"
        try:
            sm = str(anim.get_editor_property("StateMachineMoveState"))
            sm = sm.split(".")[-1].replace("NEW_ENUMERATOR", "E")
        except Exception:
            sm = "ERR"
        cur = (act, mv, tr, flag, an, sm)
        if cur != _st["prev"]:
            _st["prev"] = cur
            with open(LOG, "a") as f:
                f.write("t=%.3f n=%d act=%d mv=%d tr=%d flag=%d sm=%s anim=%s%s"
                        % (time.time() - _st["t0"], _st["n"], act, mv, tr, flag, sm, an, NL))
    except Exception as e:
        with open(LOG, "a") as f:
            f.write("EXC %r%s" % (e, NL))
        try:
            unreal.unregister_slate_post_tick_callback(mod.handle)
        except Exception:
            pass
        mod.handle = None


mod.handle = unreal.register_slate_post_tick_callback(_tick)
print("ATTACH_PROBE_ON")
