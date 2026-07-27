# 경사 Z보정 검증 프로브 — 원통 경사 오르기 팔 밀림 재현용 (2026-07-24)
# 로깅: Dz/게이트거리/타깃/손/어깨갭 + 슬라이드 상태 → slopefix.log
# 실행: 에디터 콘솔 py probe_slopefix.py (등록 후 PIE 재현)
import unreal, sys, types

for name in ("__cyl__", "__slide__", "__pcm1__", "__uph__", "__c0__", "__sfx__"):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__sfx__")
sys.modules["__sfx__"] = mod
LOG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/slopefix.log"
open(LOG, "w").close()
NL = chr(10)


def _v(o):
    return "(%.1f,%.1f,%.1f)" % (o.x, o.y, o.z)


def _d(a, b):
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
        cur = float(lmd.get_editor_property("CurrentDistance"))
        inprog = int(bool(lmd.get_editor_property("bUnitMoveInProgress")))
        fb = int(bool(lmd.get_editor_property("bFrontBlocked")))
        ang = float(lmd.get_editor_property("transit_move_angle_deg"))
        nfb = int(bool(lmd.get_editor_property("next_front_blocked")))
        sd = float(anim.get_editor_property("LedgeMoveStartDist"))
        td = float(anim.get_editor_property("LedgeMoveTargetDist"))
        wl = anim.get_editor_property("LedgeHandWorldL")
        wr = anim.get_editor_property("LedgeHandWorldR")
        al = float(anim.get_editor_property("LedgeHandIKAlphaL"))
        ar = float(anim.get_editor_property("LedgeHandIKAlphaR"))
        dzl = float(anim.get_editor_property("LedgeSlopeDzL"))
        dzr = float(anim.get_editor_property("LedgeSlopeDzR"))
        dzb = float(anim.get_editor_property("LedgeSlopeDzBody"))
        pvz = mesh.get_socket_location("pelvis").z
        hl = mesh.get_socket_location("hand_l")
        hr = mesh.get_socket_location("hand_r")
        shl = mesh.get_socket_location("upperarm_l")
        shr = mesh.get_socket_location("upperarm_r")
        seqname = "?"
        try:
            mt = anim.get_current_active_montage()
            if mt:
                seqname = "MT:" + mt.get_name()
            else:
                # SequenceEvaluator/Player 경유 — 관련 애님 자산 추적
                for prop in ("CurrentLedgeAnim", "LedgeAnim"):
                    try:
                        a = anim.get_editor_property(prop)
                        if a:
                            seqname = a.get_name()
                            break
                    except Exception:
                        pass
        except Exception:
            pass
        sp = anim.get_editor_property("LedgeSplineRef")
        spinfo = "sp=None"
        if sp:
            WS = unreal.SplineCoordinateSpace.WORLD
            cl = sp.find_location_closest_to_world_location(wl, WS)
            crr = sp.find_location_closest_to_world_location(wr, WS)
            ploc = pawn.get_actor_location()
            key = sp.find_input_key_closest_to_world_location(ploc)
            da = float(sp.get_distance_along_spline_at_spline_input_key(key))
            spinfo = "sp=%s da=%.1f gdL=%.1f gdR=%.1f" % (
                sp.get_owner().get_name()[-12:], da, _d(cl, wl), _d(crr, wr))
        _st["n"] += 1
        with open(LOG, "a") as f:
            f.write("n=%d inprog=%d fb=%d cur=%.1f sd=%.1f td=%.1f aL=%.2f aR=%.2f DzL=%.2f DzR=%.2f DzB=%.2f pvz=%.1f ang=%.0f nfb=%d anim=%s %s"
                    % (_st["n"], inprog, fb, cur, sd, td, al, ar, dzl, dzr, dzb, pvz, ang, nfb, seqname, spinfo) + NL)
            f.write("  L tgt=%s hand=%s | gap=%.1f dsh=%.1f" % (_v(wl), _v(hl), _d(wl, hl), _d(wl, shl)) + NL)
            f.write("  R tgt=%s hand=%s | gap=%.1f dsh=%.1f" % (_v(wr), _v(hr), _d(wr, hr), _d(wr, shr)) + NL)
    except Exception as e:
        with open(LOG, "a") as f:
            f.write("ERR %s" % e + NL)


mod.handle = unreal.register_slate_post_tick_callback(_tick)
print("slopefix probe ON -> " + LOG)
