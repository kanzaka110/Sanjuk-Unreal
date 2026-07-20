# 렛지 IK 디버거 v5 — 손 IK 포인트 = 소켓 어태치 실컴포넌트 (draw_debug 1프레임 지연 문제 해결)
#   구체(어태치) : hand_l/r 소켓에 스태틱메시 구체 부착 — 렌더 포즈와 완전 동기
#                  밝음=IK 활성(α≥0.5) / 어두움=비활성. L=시안, R=마젠타
#   박스/라인    : 유닛무브 중 출발(어두움)/커밋된 다음 그립(밝음, v14 게이트 통과 후) + 경로 얇은 라인
#                  월드 고정값이라 draw_debug 지연 무관
# LedgeDebug 토글 연동 (꺼지면 구체 숨김)
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

C_L_DIM = unreal.LinearColor(0.0, 0.12, 0.12, 1.0)
C_L_BRT = unreal.LinearColor(0.0, 8.0, 8.0, 1.0)
C_R_DIM = unreal.LinearColor(0.12, 0.0, 0.12, 1.0)
C_R_BRT = unreal.LinearColor(8.0, 0.0, 8.0, 1.0)
BOX_L_DIM = unreal.LinearColor(0.0, 0.35, 0.35, 1.0)
BOX_L_BRT = unreal.LinearColor(0.0, 1.0, 1.0, 1.0)
BOX_R_DIM = unreal.LinearColor(0.35, 0.0, 0.35, 1.0)
BOX_R_BRT = unreal.LinearColor(1.0, 0.0, 1.0, 1.0)
EXT = unreal.Vector(4.0, 4.0, 4.0)
ROT0 = unreal.Rotator(0, 0, 0)
_st = {"world": None, "comps": None, "mids": None}


def _make_spheres(pawn, mesh):
    sm = unreal.load_asset("/Engine/BasicShapes/Sphere")
    mat = unreal.load_asset("/Engine/BasicShapes/BasicShapeMaterial")
    comps, mids = [], []
    for sock in ("hand_l", "hand_r"):
        c = pawn.add_component_by_class(unreal.StaticMeshComponent, False, unreal.Transform(), False)
        c.set_static_mesh(sm)
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        c.set_editor_property("cast_shadow", False)
        rules = unreal.AttachmentRule.SNAP_TO_TARGET
        c.k2_attach_to_component(mesh, sock, rules, rules, unreal.AttachmentRule.KEEP_WORLD, False)
        c.set_world_scale3d(unreal.Vector(0.09, 0.09, 0.09))
        mids.append(c.create_dynamic_material_instance(0, mat))
        comps.append(c)
    return comps, mids


def _tick(dt):
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None:
            _st.update(world=None, comps=None, mids=None)
            return
        pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
        if pawn is None:
            return
        mesh = pawn.get_components_by_class(unreal.SkeletalMeshComponent)[0]
        anim = mesh.get_anim_instance()
        if anim is None:
            return
        if _st["world"] is not w or not _st["comps"] or not unreal.SystemLibrary.is_valid(_st["comps"][0]):
            _st["comps"], _st["mids"] = _make_spheres(pawn, mesh)
            _st["world"] = w
        cl, cr = _st["comps"]
        ml, mr = _st["mids"]
        dbg = True
        try:
            dbg = bool(anim.get_editor_property("LedgeDebug"))
        except Exception:
            pass
        lmd = anim.get_editor_property("LedgeMoveData")
        active = bool(lmd.get_editor_property("bActive"))
        show = dbg and active
        cl.set_visibility(show)
        cr.set_visibility(show)
        if not show:
            return
        alL = float(anim.get_editor_property("LedgeHandIKAlphaL"))
        alR = float(anim.get_editor_property("LedgeHandIKAlphaR"))
        ml.set_vector_parameter_value("Color", C_L_BRT if alL >= 0.5 else C_L_DIM)
        mr.set_vector_parameter_value("Color", C_R_BRT if alR >= 0.5 else C_R_DIM)
        # 유닛무브 마커 (월드 고정값 — draw_debug 지연 무관)
        if bool(anim.get_editor_property("bTransitMoving")):
            aL = anim.get_editor_property("LedgeHandAnchorL")
            aR = anim.get_editor_property("LedgeHandAnchorR")
            dL = anim.get_editor_property("LedgeHandDestL")
            dR = anim.get_editor_property("LedgeHandDestR")
            SL = unreal.SystemLibrary
            for a, d, dim, brt in ((aL, dL, BOX_L_DIM, BOX_L_BRT), (aR, dR, BOX_R_DIM, BOX_R_BRT)):
                SL.draw_debug_box(w, a, EXT, dim, ROT0, 0.0, 1.5)
                if (d - a).length() > 20.0:
                    SL.draw_debug_box(w, d, EXT, brt, ROT0, 0.0, 1.5)
                    SL.draw_debug_line(w, a, d, brt, 0.0, 0.2)
    except Exception as e:
        try:
            with open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/ldbg_exc.log", "a") as f:
                f.write(repr(e) + chr(10))
        except Exception:
            pass


mod.handle = unreal.register_slate_post_tick_callback(_tick)
print("LEDGE_IK_DEBUG_V5_ON")
