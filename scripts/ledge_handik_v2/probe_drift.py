import unreal, json, sys, time, types

for name in ("__ikv2__", "__ikdrift__", "__ikiso__"):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__ikdrift__")
sys.modules["__ikdrift__"] = mod
LOG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/ikdrift.log"
open(LOG, "w").close()
NL = chr(10)


def _tick(dt, _st={"t0": time.time(), "n": 0, "ph": None, "pa": None}):
    _st["n"] += 1
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
        if _st["n"] % 2 != 0:
            return
        rec = {"t": round(time.time() - _st["t0"], 3)}
        rec["aL"] = round(float(anim.get_editor_property("LedgeHandIKAlphaL")), 2)
        rec["aR"] = round(float(anim.get_editor_property("LedgeHandIKAlphaR")), 2)
        # FootPlacement 게이트 경로 검증
        for key, names in (("w", ("SmoothedFootIKWeight", "SmoothedFootIKWeight ")),
                           ("fpA", ("FootPlacementAlpha",))):
            for nm in names:
                try:
                    rec[key] = round(float(anim.get_editor_property(nm)), 3)
                    break
                except Exception:
                    rec[key] = "ERR"
        # 목표 (컴포넌트 상수 → 월드) — SB2 커스텀 클래스 API 폴백 체인
        if hasattr(mesh, "get_world_transform"):
            m2w = mesh.get_world_transform()
        elif hasattr(mesh, "k2_get_component_to_world"):
            m2w = mesh.k2_get_component_to_world()
        else:
            m2w = mesh.get_socket_transform("", unreal.RelativeTransformSpace.RTS_WORLD)
        cl = anim.get_editor_property("LedgeHandIdleCompL")
        tgtL = m2w.transform_location(cl)
        rec["tgtL"] = [round(tgtL.x, 1), round(tgtL.y, 1), round(tgtL.z, 1)]
        # 실제 손 / 액터
        hl = mesh.get_socket_location("hand_l")
        al = pawn.get_actor_location()
        rec["hL"] = [round(hl.x, 1), round(hl.y, 1), round(hl.z, 1)]
        # 판정 필드: 손 컴포넌트 좌표(원점 끌림 확인), 메시 원점, 모드, 커브
        hc = m2w.inverse_transform_location(hl)
        rec["hComp"] = [round(hc.x, 1), round(hc.y, 1), round(hc.z, 1)]
        mt = m2w.translation
        rec["mz"] = round(mt.z, 1)
        try:
            rec["fb"] = bool(anim.get_editor_property("LedgeFrontBlocked"))
        except Exception:
            rec["fb"] = "ERR"
        try:
            rec["cL"] = round(float(anim.get_curve_value("ledge_hand_ik_l")), 2)
            rec["cR"] = round(float(anim.get_curve_value("ledge_hand_ik_r")), 2)
        except Exception:
            pass
        # 오른손 풀 세트
        cr_ = anim.get_editor_property("LedgeHandIdleCompR")
        tgtR = m2w.transform_location(cr_)
        rec["tgtR"] = [round(tgtR.x, 1), round(tgtR.y, 1), round(tgtR.z, 1)]
        hr = mesh.get_socket_location("hand_r")
        rec["hR"] = [round(hr.x, 1), round(hr.y, 1), round(hr.z, 1)]
        rec["gapR"] = round((hr - tgtR).length(), 2)
        # 래치 판정 입력 (정지 임계 검증)
        try:
            vel = anim.get_editor_property("LedgeCalcVelocity")
            rec["vel"] = round(vel.length(), 0)
            rec["velX"] = round(vel.x, 1)
        except Exception:
            rec["vel"] = "ERR"
        # 무브데이터 거리 (횡축 부호 K 판정: cd 증감 vs velX 부호 상관)
        try:
            md = pawn.get_editor_property("CharacterMovement").call_method("GetLedgeMoveData")
            rec["cd"] = round(float(md.get_editor_property("CurrentDistance")), 1)
            rec["td"] = round(float(md.get_editor_property("UnitMoveTargetDistance")), 1)
            rec["sd"] = round(float(md.get_editor_property("UnitMoveStartDistance")), 1)
            rec["ip"] = 1 if bool(md.get_editor_property("bUnitMoveInProgress")) else 0
        except Exception:
            pass
        # v5/v6 체인 입력 (점프 원인 분해: mc커브 / Anchor / McBase)
        try:
            rec["mcL"] = round(float(anim.get_curve_value("ledge_hand_move_l")), 2)
            rec["mcR"] = round(float(anim.get_curve_value("ledge_hand_move_r")), 2)
            av = anim.get_editor_property("LedgeHandAnchorL")
            rec["anL"] = [round(av.x, 1), round(av.y, 1), round(av.z, 1)]
            av = anim.get_editor_property("LedgeHandAnchorR")
            rec["anR"] = [round(av.x, 1), round(av.y, 1), round(av.z, 1)]
            rec["mbL"] = round(float(anim.get_editor_property("LedgeMcBaseL")), 2)
            rec["mbR"] = round(float(anim.get_editor_property("LedgeMcBaseR")), 2)
        except Exception:
            pass
        # 팔 신전 실측 (클램프 42 작동 판정: reach==42 클램프중 / ~44.5 무클램프)
        try:
            sh = mesh.get_socket_location("upperarm_l")
            rec["reachL"] = round((hl - sh).length(), 2)
            sh = mesh.get_socket_location("upperarm_r")
            rec["reachR"] = round((hr - sh).length(), 2)
        except Exception:
            pass
        # 래치 변수 (글라이드/홀드 판정 확인)
        try:
            hw = anim.get_editor_property("LedgeHandWorldL")
            rec["hwL"] = [round(hw.x, 1), round(hw.y, 1), round(hw.z, 1)]
            hw = anim.get_editor_property("LedgeHandWorldR")
            rec["hwR"] = [round(hw.x, 1), round(hw.y, 1), round(hw.z, 1)]
        except Exception:
            pass
        # 틱 변위 — 드리프트 위상 분리 핵심
        if _st["ph"] is not None:
            rec["dHandL"] = round((hl - _st["ph"]).length(), 3)
            rec["dActor"] = round((al - _st["pa"]).length(), 3)
            rec["gapL"] = round((hl - tgtL).length(), 2)
        _st["ph"] = hl
        _st["pa"] = al
        with open(LOG, "a") as f:
            f.write(json.dumps(rec) + NL)
    except Exception as e:
        if _st["n"] % 120 == 0:
            try:
                with open(LOG, "a") as f:
                    f.write(json.dumps({"err": repr(e)[:150]}) + NL)
            except Exception:
                pass


mod.handle = unreal.register_slate_post_tick_callback(_tick)
print("IKDRIFT_PROBE_ON")
