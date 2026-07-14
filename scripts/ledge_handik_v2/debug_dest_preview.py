# 렛지 고정점 디버거 v2 — 유닛무브 시작에 래치되는 4개 고정 포인트 (네모 박스)
#   이동전 손위치(Anchor) L/R + 이동후 손위치(Dest) L/R — 이동 중 절대 안 움직여야 정상
#   실제 IK 포인트 디버거(LedgeDebugs 구체)와 구분: 고정점 = BOX
# 래치 조건: UnitMoveTargetDistance 변경(=새 유닛무브). K(횡축 부호)는 실이동으로 자동 학습
#   → ledge_ksign.log 에 기록 (ABP CF_209/210.B 동기용)
# 색: L=시안, R=마젠타 / Anchor=어두움, Dest=밝음
import unreal, sys, types

for name in ("__ldestprev__",):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__ldestprev__")
sys.modules["__ldestprev__"] = mod

CONST = {
    True: (unreal.Vector(5.23, -3.75, 167.07), unreal.Vector(-6.04, -3.14, 166.67)),
    False: (unreal.Vector(7.19, -1.85, 166.34), unreal.Vector(-7.59, -2.02, 166.21)),
}
C_L_DIM = unreal.LinearColor(0.0, 0.35, 0.35, 1.0)
C_L_BRT = unreal.LinearColor(0.0, 1.0, 1.0, 1.0)
C_R_DIM = unreal.LinearColor(0.35, 0.0, 0.35, 1.0)
C_R_BRT = unreal.LinearColor(1.0, 0.0, 1.0, 1.0)
EXT = unreal.Vector(4.0, 4.0, 4.0)
KLOG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/ledge_ksign.log"

_st = {"td": None, "anchor": None, "dest": None, "axis": None,
       "cd0": 0.0, "pos0": None, "k": -1.0, "k_locked": False}  # K=-1 실측 (ABP CF_209/210 동기)


def _tick(dt):
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
        try:
            if not bool(anim.get_editor_property("LedgeDebug")):
                return
        except Exception:
            pass
        mc = pawn.get_editor_property("CharacterMovement")
        d = mc.call_method("GetLedgeMoveData")
        if not bool(d.get_editor_property("bActive")):
            _st["td"] = None
            return
        in_prog = bool(d.get_editor_property("bUnitMoveInProgress"))
        td = float(d.get_editor_property("UnitMoveTargetDistance"))
        cd = float(d.get_editor_property("CurrentDistance"))
        fb = bool(d.get_editor_property("bFrontBlocked"))
        if hasattr(mesh, "get_world_transform"):
            m2w = mesh.get_world_transform()
        else:
            m2w = mesh.get_socket_transform("", unreal.RelativeTransformSpace.RTS_WORLD)
        cl, cr = CONST[fb]

        stale = _st["anchor"] is not None and \
            (m2w.transform_location(cl) - _st["anchor"][0]).length() > 200.0
        if in_prog and (_st["td"] != td or stale):
            # 새 유닛무브 — 래치 (이동전=현재 그립, 이동후=+횡축×잔여거리×K)
            ax = m2w.transform_direction(unreal.Vector(1, 0, 0))
            ax.z = 0.0
            ax = ax.normal()
            aL = m2w.transform_location(cl)
            aR = m2w.transform_location(cr)
            off = ax * ((td - cd) * _st["k"])
            _st.update(td=td, axis=ax, cd0=cd, pos0=m2w.translation,
                       anchor=(aL, aR), dest=(aL + off, aR + off))
        elif in_prog and not _st["k_locked"] and _st["pos0"] is not None:
            # K 자동 학습: 실제 메시 변위 vs 횡축×거리진행 상관
            delta = m2w.translation - _st["pos0"]
            delta.z = 0.0
            prog = (cd - _st["cd0"]) * _st["k"]
            if delta.length() > 12 and abs(prog) > 1:
                k_true = _st["k"] if _st["axis"].dot(delta) * prog > 0 else -_st["k"]
                with open(KLOG, "a") as f:
                    f.write("K_true=%.0f (was %.0f)\n" % (k_true, _st["k"]))
                if k_true != _st["k"]:
                    _st["k"] = k_true
                    off = _st["axis"] * ((td - cd) * k_true)
                    aL, aR = _st["anchor"]
                    _st["dest"] = (aL + off, aR + off)
                _st["k_locked"] = True

        if _st["anchor"] is not None:
            aL, aR = _st["anchor"]
            dL, dR = _st["dest"]
            unreal.SystemLibrary.draw_debug_box(w, aL, EXT, C_L_DIM, unreal.Rotator(0, 0, 0), 0.0, 1.5)
            unreal.SystemLibrary.draw_debug_box(w, aR, EXT, C_R_DIM, unreal.Rotator(0, 0, 0), 0.0, 1.5)
            unreal.SystemLibrary.draw_debug_box(w, dL, EXT, C_L_BRT, unreal.Rotator(0, 0, 0), 0.0, 1.5)
            unreal.SystemLibrary.draw_debug_box(w, dR, EXT, C_R_BRT, unreal.Rotator(0, 0, 0), 0.0, 1.5)
            unreal.SystemLibrary.draw_debug_line(w, aL, dL, C_L_BRT, 0.0, 0.4)
            unreal.SystemLibrary.draw_debug_line(w, aR, dR, C_R_BRT, 0.0, 0.4)
    except Exception:
        pass


mod.handle = unreal.register_slate_post_tick_callback(_tick)
print("LEDGE_DEST_PREVIEW_V2_ON")
