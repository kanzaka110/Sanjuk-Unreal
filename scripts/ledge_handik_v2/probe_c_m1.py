# Phase C M1 래치 검증 프로브 (2026-07-23)
# 목적: 유닛무브 중 M1 래치(LedgeSplineRef/StartDist/TargetDist/StartT) 정합 +
#       M2 예정 수학  dest = T(td) * StartT^-1 * Anchor  가 실제 도착 앵커와 일치하는지 사전 검증
# 실행: 에디터 콘솔  py "H:/내 드라이브/Claude/Sanjuk-Unreal/scripts/ledge_handik_v2/probe_c_m1.py"
import unreal, sys, types

for name in ("__cyl__", "__slide__", "__pcm1__"):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__pcm1__")
sys.modules["__pcm1__"] = mod
LOG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/pcm1.log"
open(LOG, "w").close()
NL = chr(10)


def _v(o):
    return "(%.1f,%.1f,%.1f)" % (o.x, o.y, o.z)


def _tick(dt, _st={"n": 0}):
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
        cur = float(lmd.get_editor_property("CurrentDistance"))
        inprog = int(bool(lmd.get_editor_property("bUnitMoveInProgress")))
        bt = int(bool(lmd.get_editor_property("bTransitingToNextLedge")))

        spref = anim.get_editor_property("LedgeSplineRef")
        sd = float(anim.get_editor_property("LedgeMoveStartDist"))
        td = float(anim.get_editor_property("LedgeMoveTargetDist"))
        startT = anim.get_editor_property("LedgeMoveStartT")
        anchor = anim.get_editor_property("LedgeHandAnchorL")
        predl = anim.get_editor_property("LedgeHandWorldPredL")

        spname = spref.get_owner().get_name() if spref else "None"
        dest_spl = None
        if spref:
            tT = spref.get_transform_at_distance_along_spline(
                td, unreal.SplineCoordinateSpace.WORLD)
            local_a = startT.inverse_transform_location(anchor)
            dest_spl = tT.transform_location(local_a)

        _st["n"] += 1
        with open(LOG, "a") as f:
            f.write("n=%d inprog=%d bt=%d cur=%.1f | latch sd=%.1f td=%.1f sp=%s startT=%s yaw=%.1f"
                    % (_st["n"], inprog, bt, cur, sd, td, spname,
                       _v(startT.translation), float(startT.rotation.rotator().yaw)) + NL)
            f.write("  anchorL=%s predL=%s destSPL=%s"
                    % (_v(anchor), _v(predl), _v(dest_spl) if dest_spl else "None") + NL)
    except Exception as e:
        with open(LOG, "a") as f:
            f.write("ERR %s" % e + NL)


mod.handle = unreal.register_slate_post_tick_callback(_tick)
print("pcm1 probe ON -> " + LOG)
