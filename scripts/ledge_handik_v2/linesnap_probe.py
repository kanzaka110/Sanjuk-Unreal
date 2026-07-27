# LineSnap 검증 프로브 (2026-07-25) — 타깃/앵커의 라인 Z 잔차 정량화 → linesnap.log
# 판별: SnapDz 항상 0 = 함수 미작동(게이트/호출) | SnapDz 정상인데 잔차 큼 = 주입점이 실효 경로 아님
import unreal, sys, types

for name in ("__cyl__", "__slide__", "__pcm1__", "__uph__", "__c0__", "__sfx__", "__lsn__"):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__lsn__")
sys.modules["__lsn__"] = mod
LOG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/linesnap.log"
open(LOG, "w").close()
NL = chr(10)
C0L, C0R = -8.66, -8.79


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
        inprog = int(bool(lmd.get_editor_property("bUnitMoveInProgress")))
        ang = float(lmd.get_editor_property("transit_move_angle_deg"))
        snl = float(anim.get_editor_property("LedgeSnapDzL"))
        snr = float(anim.get_editor_property("LedgeSnapDzR"))
        anl = anim.get_editor_property("LedgeHandAnchorL")
        anr = anim.get_editor_property("LedgeHandAnchorR")
        wl = anim.get_editor_property("LedgeHandWorldL")
        wr = anim.get_editor_property("LedgeHandWorldR")
        al = float(anim.get_editor_property("LedgeHandIKAlphaL"))
        ar = float(anim.get_editor_property("LedgeHandIKAlphaR"))
        hl = mesh.get_socket_location("hand_l")
        hr = mesh.get_socket_location("hand_r")
        sp = anim.get_editor_property("LedgeSplineRef")
        res = "sp=None"
        if sp:
            WS = unreal.SplineCoordinateSpace.WORLD

            def rz(p, c0):
                cl = sp.find_location_closest_to_world_location(p, WS)
                return (cl.z + c0) - p.z  # 잔차: 0이면 라인 위

            res = "resAnc L=%.2f R=%.2f resTgt L=%.2f R=%.2f resHand L=%.2f R=%.2f" % (
                rz(anl, C0L), rz(anr, C0R), rz(wl, C0L), rz(wr, C0R), rz(hl, C0L), rz(hr, C0R))
        _st["n"] += 1
        gzl = hl.z - wl.z
        gzr = hr.z - wr.z
        with open(LOG, "a") as f:
            f.write("n=%d inprog=%d ang=%.0f SnapDz L=%.2f R=%.2f aL=%.2f aR=%.2f gapZ L=%.2f R=%.2f %s" %
                    (_st["n"], inprog, ang, snl, snr, al, ar, gzl, gzr, res) + NL)
            f.write("  tgtL=%s tgtR=%s handL=%s handR=%s" % (_v(wl), _v(wr), _v(hl), _v(hr)) + NL)
    except Exception as e:
        with open(LOG, "a") as f:
            f.write("ERR %s" % e + NL)


mod.handle = unreal.register_slate_post_tick_callback(_tick)
print("linesnap probe ON -> " + LOG)
