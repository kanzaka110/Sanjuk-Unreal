# 원통(곡면) 렛지 이동 프로브 (2026-07-23 팔다리 꼬임 진단)
# 목적: 곡면 스플라인 유닛무브 중
#   ① 직선 외삽 도착지 (Anchor - UnitMoveVec, 현행)
#   ② TransitMoveData 기반 도착지 (TargetT * StartT^-1 * Anchor, 후보 처방)
#   를 프레임 단위로 실측 대조 -> cyl.log
# 실행: 에디터 콘솔에서  py "H:/내 드라이브/Claude/Sanjuk-Unreal/scripts/ledge_handik_v2/probe_cyl_transit.py"
import unreal, sys, time, types

for name in ("__ikv2__", "__ikdrift__", "__ikiso__", "__atprobe__", "__hover__",
             "__bodyp__", "__over__", "__slide__", "__pump__", "__pop__", "__cyl__"):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__cyl__")
sys.modules["__cyl__"] = mod
LOG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/cyl.log"
open(LOG, "w").close()
NL = chr(10)


def _v(o):
    return "(%.1f,%.1f,%.1f)" % (o.x, o.y, o.z)


def _xform_point(loc, rot, p, inverse=False):
    t = unreal.Transform(rotation=rot, location=loc, scale=unreal.Vector(1, 1, 1))
    if inverse:
        return t.inverse_transform_location(p)
    return t.transform_location(p)


def _dist(a, b):
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2) ** 0.5


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
        mc = pawn.get_movement_component()
        tmd = mc.get_transit_move_data()

        cur = float(lmd.get_editor_property("CurrentDistance"))
        td = float(lmd.get_editor_property("UnitMoveTargetDistance"))
        sd = float(lmd.get_editor_property("UnitMoveStartDistance"))
        inprog = int(bool(lmd.get_editor_property("bUnitMoveInProgress")))
        bt = int(bool(lmd.get_editor_property("bTransitingToNextLedge")))
        fb = int(bool(lmd.get_editor_property("bFrontBlocked")))

        tact = int(bool(tmd.get_editor_property("bActive")))
        sloc = tmd.get_editor_property("StartLocation")
        srot = tmd.get_editor_property("StartRotation")
        tloc = tmd.get_editor_property("TargetLocation")
        trot = tmd.get_editor_property("TargetRotation")
        irot = int(bool(tmd.get_editor_property("bInterpolateRotation")))
        fmd = int(bool(tmd.get_editor_property("bFaceMovementDirection")))
        el = float(tmd.get_editor_property("ElapsedTime"))
        du = float(tmd.get_editor_property("Duration"))

        anchor = anim.get_editor_property("LedgeHandAnchorL")
        vec = anim.get_editor_property("LedgeUnitMoveVec")
        predl = anim.get_editor_property("LedgeHandWorldPredL")
        worldl = anim.get_editor_property("LedgeHandWorldL")

        # ① 현행 직선 외삽 도착지
        dest_lin = unreal.Vector(anchor.x - vec.x, anchor.y - vec.y, anchor.z - vec.z)
        # ② TransitMoveData 강체 변환 도착지: TargetT * (StartT^-1 * Anchor)
        local_a = _xform_point(sloc, srot, anchor, inverse=True)
        dest_tmd = _xform_point(tloc, trot, local_a)

        actor_loc = pawn.get_actor_location()
        actor_yaw = float(pawn.get_actor_rotation().yaw)

        _st["n"] += 1
        with open(LOG, "a") as f:
            f.write(
                "n=%d inprog=%d bt=%d fb=%d cur=%.1f sd=%.1f td=%.1f | tmd act=%d el=%.2f/%.2f irot=%d fmd=%d"
                % (_st["n"], inprog, bt, fb, cur, sd, td, tact, el, du, irot, fmd) + NL)
            f.write("  body=%s yaw=%.1f sloc=%s syaw=%.1f tloc=%s tyaw=%.1f"
                    % (_v(actor_loc), actor_yaw, _v(sloc), float(srot.yaw), _v(tloc), float(trot.yaw)) + NL)
            f.write("  anchorL=%s vec=%s worldL=%s predL=%s" % (_v(anchor), _v(vec), _v(worldl), _v(predl)) + NL)
            f.write("  destLIN=%s destTMD=%s dLINvsTMD=%.1f"
                    % (_v(dest_lin), _v(dest_tmd), _dist(dest_lin, dest_tmd)) + NL)
    except Exception as e:
        with open(LOG, "a") as f:
            f.write("ERR %s" % e + NL)


mod.handle = unreal.register_slate_post_tick_callback(_tick)
print("cyl probe ON -> " + LOG)
