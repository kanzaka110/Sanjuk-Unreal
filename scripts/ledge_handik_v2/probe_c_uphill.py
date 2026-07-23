# Phase C 오르막 원통 — 팔 미추종 진단 프로브 (2026-07-23)
# 가설: 오르막에서 타깃 Z 선행 → 어깨 리치(벽43.8/wallless55) 3D 포화 또는 Rxy(√(R²−dz²)) 붕괴
# 로깅: 타깃(predL/R) vs 어깨(upperarm) vs 실제 손본(hand) — dz, 3D거리, 손-타깃 갭
# 실행: 에디터 콘솔  py "H:/내 드라이브/Claude/Sanjuk-Unreal/scripts/ledge_handik_v2/probe_c_uphill.py"
import unreal, sys, types

for name in ("__cyl__", "__slide__", "__pcm1__", "__uph__"):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__uph__")
sys.modules["__uph__"] = mod
LOG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/uphill.log"
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

        predl = anim.get_editor_property("LedgeHandWorldPredL")
        predr = anim.get_editor_property("LedgeHandWorldPredR")
        al = float(anim.get_editor_property("LedgeHandIKAlphaL"))
        ar = float(anim.get_editor_property("LedgeHandIKAlphaR"))
        shl = mesh.get_socket_location("upperarm_l")
        shr = mesh.get_socket_location("upperarm_r")
        hl = mesh.get_socket_location("hand_l")
        hr = mesh.get_socket_location("hand_r")
        sd = float(anim.get_editor_property("LedgeMoveStartDist"))
        td = float(anim.get_editor_property("LedgeMoveTargetDist"))
        sp = anim.get_editor_property("LedgeSplineRef")
        anchor = anim.get_editor_property("LedgeHandAnchorL")
        startT = anim.get_editor_property("LedgeMoveStartT")
        umv = anim.get_editor_property("LedgeUnitMoveVec")
        ta = int(bool(anim.get_editor_property("LedgeTransitActive")))
        spname = sp.get_owner().get_name()[-12:] if sp else "None"
        spinfo = ""
        if sp:
            ploc = pawn.get_actor_location()
            key = sp.find_input_key_closest_to_world_location(ploc)
            da = float(sp.get_distance_along_spline_at_spline_input_key(key))
            ttd = sp.get_transform_at_distance_along_spline(td, unreal.SplineCoordinateSpace.WORLD)
            rot = ttd.rotation.rotator()
            # 구 체인 도착지 (α=1 기준): anchor − umv
            old_d = unreal.Vector(anchor.x - umv.x, anchor.y - umv.y, anchor.z - umv.z)
            # 신 체인 도착지 (yaw-only): yawT(td) × yawT(sd)^-1 × anchor
            def yawT(t):
                r0 = t.rotation.rotator()
                return unreal.Transform(rotation=unreal.Rotator(0.0, 0.0, r0.yaw),
                                        location=t.translation, scale=unreal.Vector(1, 1, 1))
            tsd = sp.get_transform_at_distance_along_spline(sd, unreal.SplineCoordinateSpace.WORLD)
            new_d = yawT(ttd).transform_location(yawT(tsd).inverse_transform_location(anchor))
            spinfo = " sp=%s ta=%d da(body)=%.1f fTd=%s p=%.1f y=%.1f r=%.1f stT=%s oldD=%s newD=%s" % (
                spname, ta, da, _v(ttd.translation),
                float(rot.pitch), float(rot.yaw), float(rot.roll), _v(startT.translation),
                _v(old_d), _v(new_d))

        _st["n"] += 1
        with open(LOG, "a") as f:
            f.write("n=%d inprog=%d fb=%d cur=%.1f sd=%.1f td=%.1f aL=%.2f aR=%.2f%s"
                    % (_st["n"], inprog, fb, cur, sd, td, al, ar, spinfo) + NL)
            f.write("  L tgt=%s sh=%s hand=%s | dz=%.1f d3=%.1f gap=%.1f"
                    % (_v(predl), _v(shl), _v(hl),
                       predl.z - shl.z, _d(predl, shl), _d(predl, hl)) + NL)
            f.write("  R tgt=%s sh=%s hand=%s | dz=%.1f d3=%.1f gap=%.1f"
                    % (_v(predr), _v(shr), _v(hr),
                       predr.z - shr.z, _d(predr, shr), _d(predr, hr)) + NL)
    except Exception as e:
        with open(LOG, "a") as f:
            f.write("ERR %s" % e + NL)


mod.handle = unreal.register_slate_post_tick_callback(_tick)
print("uphill probe ON -> " + LOG)
