# 경사 Z보정 사전실측 — C0 = 그립Z(LedgeHandWorldL/R) − 스플라인 최근접점Z (평지 기준상수)
# + 몸 기준: 액터Z − 스플라인Z (펠비스 보정 기준), 스플라인 경사(탄젠트 Z)
# 사용: 프로브 등록 후 PIE에서 평지 렛지(봉/벽) 아이들 매달림 → c0flat.log 분석
# 실행: 에디터 콘솔 py "H:/내 드라이브/Claude/Sanjuk-Unreal/scripts/ledge_handik_v2/probe_c0_flat.py"
import unreal, sys, types

for name in ("__cyl__", "__slide__", "__pcm1__", "__uph__", "__c0__"):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__c0__")
sys.modules["__c0__"] = mod
LOG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/c0flat.log"
open(LOG, "w").close()
NL = chr(10)


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
        sp = anim.get_editor_property("LedgeSplineRef")
        if sp is None:
            return
        fb = int(bool(lmd.get_editor_property("bFrontBlocked")))
        inprog = int(bool(lmd.get_editor_property("bUnitMoveInProgress")))
        wl = anim.get_editor_property("LedgeHandWorldL")
        wr = anim.get_editor_property("LedgeHandWorldR")
        al = float(anim.get_editor_property("LedgeHandIKAlphaL"))
        ar = float(anim.get_editor_property("LedgeHandIKAlphaR"))
        WS = unreal.SplineCoordinateSpace.WORLD
        cl = sp.find_location_closest_to_world_location(wl, WS)
        cr = sp.find_location_closest_to_world_location(wr, WS)
        ploc = pawn.get_actor_location()
        cb = sp.find_location_closest_to_world_location(ploc, WS)
        # 경사도: 몸 최근접 아크의 탄젠트 Z 성분 (정규화)
        key = sp.find_input_key_closest_to_world_location(ploc)
        da = float(sp.get_distance_along_spline_at_spline_input_key(key))
        tan = sp.get_tangent_at_distance_along_spline(da, WS)
        tlen = max(1e-6, (tan.x ** 2 + tan.y ** 2 + tan.z ** 2) ** 0.5)
        slope = tan.z / tlen
        _st["n"] += 1
        with open(LOG, "a") as f:
            f.write(
                "n=%d fb=%d inprog=%d aL=%.2f aR=%.2f slope=%.3f | "
                "c0L=%.2f c0R=%.2f bodyRelZ=%.2f | wLz=%.1f splLz=%.1f wRz=%.1f splRz=%.1f pz=%.1f splBz=%.1f da=%.1f"
                % (_st["n"], fb, inprog, al, ar, slope,
                   wl.z - cl.z, wr.z - cr.z, ploc.z - cb.z,
                   wl.z, cl.z, wr.z, cr.z, ploc.z, cb.z, da) + NL)
    except Exception as e:
        with open(LOG, "a") as f:
            f.write("ERR %s" % e + NL)


mod.handle = unreal.register_slate_post_tick_callback(_tick)
print("c0 probe ON -> " + LOG)
