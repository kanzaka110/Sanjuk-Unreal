# 발목 꺾임 프로브 — 렛지 이동 모션 교체 구간 (2026-07-21)
# 판정 대상: 이펙터 회전=애님 발 글로벌 고정 → IK로 calf가 돌면 발목 로컬 각도가 그만큼 꺾이는가.
# 매 2틱: FootAlpha / 발목 로컬 각도(foot 기준 calf) / calf 글로벌 / 타깃 갭 / 신전 리치(클램프 76 대비)
# 실행: 에디터 콘솔  py "H:/내 드라이브/Claude/Sanjuk-Unreal/scripts/ledge_handik_v2/probe_ankle.py"
# 중지: 같은 스크립트 재실행(자동 언레지스터) 또는 py "...probe_ankle.py" 후 PIE 종료
import unreal, json, sys, time, types

for name in ("__ikv2__", "__ikdrift__", "__ikiso__", "__ankle__"):
    m = sys.modules.get(name)
    if m is not None and getattr(m, "handle", None) is not None:
        try:
            unreal.unregister_slate_post_tick_callback(m.handle)
        except Exception:
            pass
        m.handle = None

mod = types.ModuleType("__ankle__")
sys.modules["__ankle__"] = mod
LOG = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/ankle.log"
open(LOG, "w").close()
NL = chr(10)
REACH_CLAMP = 76.0


def _xf(mesh, bone):
    return mesh.get_socket_transform(bone, unreal.RelativeTransformSpace.RTS_WORLD)


def _rot_euler(t):
    q = t.rotation
    try:
        r = q.rotator()
    except Exception:
        r = unreal.MathLibrary.quat_rotator(q)
    return [round(r.roll, 1), round(r.pitch, 1), round(r.yaw, 1)]


def _local_ankle(mesh, side):
    # 발목 로컬 = calf 기준 foot 상대 회전. IK 무관하게 애님이면 거의 일정해야 정상.
    foot = _xf(mesh, "foot_" + side)
    calf = _xf(mesh, "calf_" + side)
    rel = unreal.MathLibrary.compose_transforms(foot, unreal.MathLibrary.invert_transform(calf))
    return _rot_euler(rel), _rot_euler(calf), foot.translation


def _get(anim, name, default=None):
    try:
        return anim.get_editor_property(name)
    except Exception:
        return default


def _tick(dt, _st={"t0": time.time(), "n": 0, "base": {}}):
    _st["n"] += 1
    try:
        w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
        if w is None:
            return
        pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
        if pawn is None:
            return
        comps = pawn.get_components_by_class(unreal.SkeletalMeshComponent)
        if not comps:
            return
        mesh = comps[0]
        anim = mesh.get_anim_instance()
        if anim is None:
            return
        if _st["n"] % 2 != 0:
            return

        rec = {"t": round(time.time() - _st["t0"], 3)}
        active = False
        for side, sfx in (("l", "L"), ("r", "R")):
            a = _get(anim, "LedgeFootIKAlpha" + sfx, 0.0)
            a = float(a or 0.0)
            if a > 0.001:
                active = True
            ankle, calf, footw = _local_ankle(mesh, side)
            tgt = _get(anim, "LedgeFootWorld" + sfx)
            thigh = _xf(mesh, "thigh_" + side).translation
            rec["a" + sfx] = round(a, 3)
            rec["ank" + sfx] = ankle            # 발목 로컬 (핵심 지표)
            rec["calf" + sfx] = calf            # calf 글로벌 (꺾임 원인 후보)
            if tgt is not None:
                # ⚠ FootTarget 은 ball 이 도달해야 할 지점이다 (CR: ToeConv = Target - (ball_anim - foot_anim)).
                #   따라서 foot 기준 gap 은 발 길이만큼 벌어지는 게 정상 — 실제 구속 오차는 ballgap 으로 본다.
                ballw = _xf(mesh, "ball_" + side).translation
                bgap = unreal.Vector(tgt.x - ballw.x, tgt.y - ballw.y, tgt.z - ballw.z)
                gap = unreal.Vector(tgt.x - footw.x, tgt.y - footw.y, tgt.z - footw.z)
                reach = unreal.Vector(tgt.x - thigh.x, tgt.y - thigh.y, tgt.z - thigh.z)
                rec["bgap" + sfx] = round(bgap.length(), 1)    # ★ 실제 접지 오차 (ball ↔ 타깃)
                rec["gap" + sfx] = round(gap.length(), 1)      # L(14.95)이면 IK 도달 성공, 벗어나면 도달 실패
                rec["rch" + sfx] = round(reach.length(), 1)    # 신전거리 (>=76 이면 클램프 발동)
                # 타깃 점프 시점 추적: 이전 프레임 대비 타깃 이동량 (알파 하강보다 먼저 튀는지 판정)
                # 외삽 적용 후: CR 이 실제 소비하는 건 Pred. 보정 효과는 이 기준으로 봐야 보인다.
                prd = _get(anim, "LedgeFootWorldPred" + sfx)
                if prd is not None:
                    pg = unreal.Vector(prd.x - ballw.x, prd.y - ballw.y, prd.z - ballw.z)
                    rec["pgap" + sfx] = round(pg.length(), 1)   # ★ 외삽 타깃 ↔ ball
                    # lead = 외삽이 실제로 얼마나 걸렸나. 0 이면 처방이 안 먹은 것 (prev 가 같은 프레임에 갱신 등)
                    ld = unreal.Vector(prd.x - tgt.x, prd.y - tgt.y, prd.z - tgt.z)
                    rec["lead" + sfx] = round(ld.length(), 2)
                pw = _get(anim, "LedgePrevFootWorld" + sfx)
                if pw is not None:
                    # world - prev 를 직접 확인 (프레임당 실제 타깃 이동량)
                    dw = unreal.Vector(tgt.x - pw.x, tgt.y - pw.y, tgt.z - pw.z)
                    rec["dw" + sfx] = round(dw.length(), 2)
                pv = _st.setdefault("ptgt", {}).get(sfx)
                if pv is not None:
                    rec["tmv" + sfx] = round(unreal.Vector(tgt.x - pv[0], tgt.y - pv[1], tgt.z - pv[2]).length(), 1)
                _st["ptgt"][sfx] = (tgt.x, tgt.y, tgt.z)
            # 커브 원본 (전환 감지용)
            try:
                rec["c" + sfx] = round(float(anim.get_curve_value("ledge_foot_ik_" + side)), 2)
            except Exception:
                pass
            # 알파 0 구간의 발목 각도를 기준선으로 축적 (애님 원본 = IK 미개입)
            if a <= 0.001:
                _st["base"][sfx] = ankle
            elif sfx in _st["base"]:
                b = _st["base"][sfx]
                rec["dev" + sfx] = [round(ankle[i] - b[i], 1) for i in range(3)]  # 기준선 대비 발목 편차

        if not active and not _st["base"]:
            return
        with open(LOG, "a") as fp:
            fp.write(json.dumps(rec) + NL)
    except Exception:
        import traceback
        # 예외를 조용히 삼키면 재현을 통째로 날린다 (2026-07-21 math 미import 로 777프레임 전멸)
        # → 5회 넘으면 스스로 멈추고 로그 맨 앞에 눈에 띄게 남긴다
        _st["err"] = _st.get("err", 0) + 1
        with open(LOG, "a") as fp:
            fp.write("ERR " + traceback.format_exc().replace(NL, " | ")[:400] + NL)
            if _st["err"] >= 5:
                fp.write("!!! PROBE ABORTED — 위 예외가 5회 반복. 스크립트 고치고 다시 실행할 것 !!!" + NL)
        if _st["err"] >= 5 and mod.handle is not None:
            try:
                unreal.unregister_slate_post_tick_callback(mod.handle)
            except Exception:
                pass
            mod.handle = None


mod.handle = unreal.register_slate_post_tick_callback(_tick)
print("ANKLE_PROBE_ON -> " + LOG)
