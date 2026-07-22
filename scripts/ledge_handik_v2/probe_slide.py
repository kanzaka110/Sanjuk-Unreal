# 슬라이드 타깃 체인 프로브 (2026-07-22 Phase2 검증)
# 목적: 손L 타깃 = Lerp(AnchorL, AnchorL-UnitMoveVec, renorm(move_l)) 이 런타임에서 실제로 계산되는지
#        단계별 값(커브/McBase/Anchor/Vec/WorldL/PredL) 프레임 단위 대조 -> slide.log
# 실행: 에디터 콘솔에서  py "H:/내 드라이브/Claude/Sanjuk-Unreal/scripts/ledge_handik_v2/probe_slide.py"
import unreal, sys, time, types

for name in ("__ikv2__", "__ikdrift__", "__ikiso__", "__atprobe__", "__hover__", "__bodyp__", "__over__", "__slide__"):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__slide__")
sys.modules["__slide__"] = mod
LOG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/slide.log"
open(LOG, "w").close()
NL = chr(10)
ANIMF = "Anim_3_CE8F6C8948855759C43A24A538203DDC"


def _v(o):
    return "(%.1f,%.1f,%.1f)" % (o.x, o.y, o.z)


def _lerp(a, b, t):
    return unreal.Vector(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, a.z + (b.z - a.z) * t)


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
        a = anim.get_editor_property("BlendStackInputs").get_editor_property(ANIMF)
        an = a.get_name() if a else "None"
        mv = float(anim.get_curve_value("ledge_hand_move_l"))
        ik = float(anim.get_curve_value("ledge_hand_ik_l"))
        aL = float(anim.get_editor_property("LedgeHandIKAlphaL"))
        cur = float(lmd.get_editor_property("CurrentDistance"))
        td = float(lmd.get_editor_property("UnitMoveTargetDistance"))
        inprog = int(bool(lmd.get_editor_property("bUnitMoveInProgress")))
        mcb = float(anim.get_editor_property("LedgeMcBaseL"))
        anchor = anim.get_editor_property("LedgeHandAnchorL")
        vec = anim.get_editor_property("LedgeUnitMoveVec")
        worldl = anim.get_editor_property("LedgeHandWorldL")
        predl = anim.get_editor_property("LedgeHandWorldPredL")
        destl = anim.get_editor_property("LedgeHandDestL")
        hand = mesh.get_socket_location("hand_l")
        alpha = max(0.0, min(1.0, (mv - mcb) / max(1.0 - mcb, 0.001)))
        expb = unreal.Vector(anchor.x - vec.x, anchor.y - vec.y, anchor.z - vec.z)
        expt = _lerp(anchor, expb, alpha)
        dxy = ((worldl.x - expt.x) ** 2 + (worldl.y - expt.y) ** 2) ** 0.5
        line = "t=%.2f an=%s mv=%.3f ik=%.2f aL=%.2f cur=%.1f td=%.1f ip=%d mcb=%.3f alpha=%.3f%s  anc=%s vec=%s expB=%s expT=%s worldL=%s dXY=%.1f%s  predL=%s destL=%s hand=%s" % (
            time.time() - _st["t0"], an, mv, ik, aL, cur, td, inprog, mcb, alpha, NL,
            _v(anchor), _v(vec), _v(expb), _v(expt), _v(worldl), dxy, NL,
            _v(predl), _v(destl), _v(hand))
        with open(LOG, "a") as f:
            f.write(line + NL)
    except Exception as e:
        with open(LOG, "a") as f:
            f.write("ERR " + repr(e)[:200] + NL)


mod.handle = unreal.register_slate_post_tick_callback(_tick)
print("SLIDE PROBE ON -> " + LOG)
print("PIE에서 Wallless 이동 몇 번 후, 콘솔에 py \"...probe_slide.py\" 다시 실행하면 이전 콜백 해제됨")
