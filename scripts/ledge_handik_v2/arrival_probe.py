# 도착 틤 진단 프로브 v2 (2026-07-27) — Ledge_HandFinal z소스 Select(CF_78) 입력 전수 로깅 → arrival.log
# 목적: 도착 프레임 타깃 ±167cm 텔레포트의 소스 특정 (메시포즈 경로 CF_96 vs 슬라이드 경로 CF_121)
# A경로 재현: MeshToWorld × (FBLatch ? (5.23,-3.75,167.07) : (7.19,-1.85,166.34))
import unreal, sys, types

for name in ("__cyl__", "__slide__", "__pcm1__", "__uph__", "__c0__", "__sfx__", "__lsn__", "__arv__"):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__arv__")
sys.modules["__arv__"] = mod
LOG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/arrival.log"
open(LOG, "w").close()
NL = chr(10)
LOC_A = unreal.Vector(5.23, -3.75, 167.07)
LOC_B = unreal.Vector(7.19, -1.85, 166.34)


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
        _st["n"] += 1
        inprog = int(bool(lmd.get_editor_property("bUnitMoveInProgress")))
        cur = float(lmd.get_editor_property("CurrentDistance"))
        umtd = float(lmd.get_editor_property("UnitMoveTargetDistance"))
        ta = int(bool(anim.get_editor_property("LedgeTransitActive")))
        fb = int(bool(anim.get_editor_property("LedgeFBLatch")))
        sd = float(anim.get_editor_property("LedgeMoveStartDist"))
        td = float(anim.get_editor_property("LedgeMoveTargetDist"))
        m2w = anim.get_editor_property("LedgeMeshToWorld")
        # A경로 재현 (CF_96)
        loc = LOC_A if fb else LOC_B
        pathA = m2w.transform_location(loc)
        m2w_org = m2w.translation
        real_org = mesh.get_world_location()
        mst = anim.get_editor_property("LedgeMoveStartT").translation
        dtd = float(anim.get_editor_property("LedgeDestTd"))
        cvl = float(anim.get_curve_value("ledge_hand_move_l"))
        cvr = float(anim.get_curve_value("ledge_hand_move_r"))
        mbl = float(anim.get_editor_property("LedgeMcBaseL"))
        mbr = float(anim.get_editor_property("LedgeMcBaseR"))
        anl = anim.get_editor_property("LedgeHandAnchorL")
        umv = anim.get_editor_property("LedgeUnitMoveVec")
        stl = anim.get_editor_property("LedgeSlideTgtHL")
        wl = anim.get_editor_property("LedgeHandWorldL")
        pwl = anim.get_editor_property("LedgePrevWorldNowL")
        anr = anim.get_editor_property("LedgeHandAnchorR")
        wr = anim.get_editor_property("LedgeHandWorldR")
        al = float(anim.get_editor_property("LedgeHandIKAlphaL"))
        ar = float(anim.get_editor_property("LedgeHandIKAlphaR"))
        sp = anim.get_editor_property("LedgeSplineRef")
        spz = -999.0
        if sp:
            WS = unreal.SplineCoordinateSpace.WORLD
            spz = sp.find_location_closest_to_world_location(anl, WS).z
        with open(LOG, "a") as f:
            f.write("n=%d ip=%d ta=%d fb=%d sd=%.1f td=%.1f spz=%.1f dtd=%.1f cvl=%.3f cvr=%.3f mbl=%.3f mbr=%.3f cur=%.1f umtd=%.1f mst=%s" %
                    (_st["n"], inprog, ta, fb, sd, td, spz, dtd, cvl, cvr, mbl, mbr, cur, umtd, _v(mst)) + NL)
            f.write("  A=%s m2wOrg=%s realOrg=%s" % (_v(pathA), _v(m2w_org), _v(real_org)) + NL)
            f.write("  anchL=%s umv=%s slideL=%s prevL=%s outL=%s" % (_v(anl), _v(umv), _v(stl), _v(pwl), _v(wl)) + NL)
            f.write("  anchR=%s outR=%s aL=%.2f aR=%.2f" % (_v(anr), _v(wr), al, ar) + NL)
    except Exception as e:
        with open(LOG, "a") as f:
            f.write("ERR %s" % e + NL)


mod.handle = unreal.register_slate_post_tick_callback(_tick)
print("arrival probe ON -> " + LOG)
