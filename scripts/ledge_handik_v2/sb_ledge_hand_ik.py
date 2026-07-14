# sb_ledge_hand_ik.py — AM_SBLedgeHandIK 코어 로직
# 렛지 셔플 애님의 hand_l/hand_r 본 궤적을 샘플해 플라이트(손 이동) 구간을 검출하고
# ledge_hand_ik_l / ledge_hand_ik_r 커브(1=플랜트/핀 허용, 0=플라이트/핀 해제)를 베이크한다.
# 검출 기준: 프레임간 손 변위 속도 > FlightSpeedThreshold (cm/s).
# 실측 근거 (P_Player_Ledge_Move_ShortL_Wallless, 30fps):
#   플랜트 중 바디 드리프트 ~105 cm/s, 플라이트 225~276 cm/s → 기본 문턱 140 cm/s
import unreal

MODIFIER_CLASS_NAME = "AM_SBLedgeHandIK"

DEFAULTS = {
    "FlightSpeedThreshold": 140.0,  # cm/s — 이 속도 초과 프레임 = 플라이트
    "PlantRampFrames": 3,           # 플라이트 종료 → 1 복귀 램프 (프레임, 스무스텝 샘플)
    "ReleaseRampFrames": 2,         # 1 → 0 릴리즈 램프 (프레임, 스무스텝 샘플)
    "MinFlightFrames": 2,           # 이보다 짧은 플라이트 구간은 노이즈로 무시
    "PelvisMinSpeed": 60.0,         # cm/s — 애님 내 펠비스 최대속도가 이 미만이면 커브 0 (아이들 노이즈 가드)
    "PelvisFallFrames": 6,          # 펠비스 스프링 커브 하강 스무딩 (상승은 즉시)
}

HANDS = (("hand_l", "ledge_hand_ik_l", "ledge_hand_move_l"),
         ("hand_r", "ledge_hand_ik_r", "ledge_hand_move_r"))
PELVIS_BONE = "pelvis"
PELVIS_CURVE = "ledge_pelvis_spring"
ALL_CURVES = tuple(c for _, c, _ in HANDS) + tuple(m for _, _, m in HANDS) + (PELVIS_CURVE,)


def _log(msg):
    unreal.log("[LedgeHandIK] " + str(msg))


def _read_params(seq):
    """에셋에 붙은 AM_SBLedgeHandIK 인스턴스의 프로퍼티를 읽고, 없으면 DEFAULTS."""
    params = dict(DEFAULTS)
    try:
        ud = seq.get_asset_user_data_of_class(unreal.AnimationModifiersAssetUserData)
        if ud:
            for inst in ud.get_editor_property("animation_modifier_instances"):
                if MODIFIER_CLASS_NAME in str(type(inst).__name__) or \
                   MODIFIER_CLASS_NAME in str(inst.get_class().get_name()):
                    for key in params:
                        try:
                            params[key] = inst.get_editor_property(key)
                        except Exception:
                            pass
                    break
    except Exception as e:
        _log("param read fallback to defaults: %r" % e)
    return params


def _sample_bone_positions(seq, num_frames, duration, bones):
    """프레임별 본 월드(컴포넌트) 위치. returns {bone: [Vector,...]}"""
    opts = unreal.AnimPoseEvaluationOptions()
    out = {b: [] for b in bones}
    for f in range(int(num_frames) + 1):
        t = duration * f / max(1, num_frames)
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(seq, t, opts)
        for bone in bones:
            tf = unreal.AnimPoseExtensions.get_bone_pose(pose, bone, unreal.AnimPoseSpaces.WORLD)
            out[bone].append(tf.translation)
    return out


def _pelvis_spring_values(positions, fps, min_speed, fall_frames):
    """펠비스 속도를 애님별 최대값으로 정규화한 0~1 엔벨로프.

    상승 즉시 / 하강 1/fall_frames 스텝. 최대속도 < min_speed 면 전부 0 (아이들 가드).
    프레임당 1키(고유 프레임)라 중복 어설션 위험 없음.
    """
    speeds = [0.0]
    for i in range(1, len(positions)):
        speeds.append((positions[i] - positions[i - 1]).length() * fps)
    speeds[0] = speeds[1] if len(speeds) > 1 else 0.0
    mx = max(speeds)
    if mx < min_speed:
        return [0.0] * len(speeds)
    fall = 1.0 / max(1, fall_frames)
    out, prev = [], 0.0
    for s in speeds:
        v = s / mx
        prev = v if v > prev else max(v, prev - fall)
        out.append(round(prev, 4))
    return out


def _flight_windows(positions, fps, threshold_cms, min_frames):
    """변위 속도 기반 플라이트 구간 [(start_f, end_f), ...] — d[i]=구간 (i-1,i] 의 이동."""
    speeds = [0.0]
    for i in range(1, len(positions)):
        d = positions[i] - positions[i - 1]
        speeds.append(d.length() * fps)
    windows, start = [], None
    for i, s in enumerate(speeds):
        if s > threshold_cms and start is None:
            start = i
        elif s <= threshold_cms and start is not None:
            if i - start >= min_frames:
                windows.append((start, i - 1))
            start = None
    if start is not None and len(speeds) - start >= min_frames:
        windows.append((start, len(speeds) - 1))
    return windows, speeds


def _build_keys(windows, num_frames, fps, plant_ramp, release_ramp):
    """윈도우 목록 → (times, values). 1=플랜트, 0=플라이트.

    ⚠ 같은 프레임에 키 2개 = UAnimSequencerController::SetCurveControlKey 어설션
    (에디터 즉사, 2026-07-13 실측). 창 병합 + 정수 프레임 dict 로 중복을 원천 차단한다.
    """
    if not windows:
        return [0.0], [1.0]

    # 1) 램프가 겹치는 창 병합 — 간격 <= plant+release 면 한 플라이트로 취급
    merged = []
    for s, e in windows:
        if merged and (s - merged[-1][1]) <= (plant_ramp + release_ramp):
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))

    # 2) 정수 프레임 키맵 — 충돌 시 0(해제) 우선
    keys = {}

    def put(frame, value):
        f = max(0, min(int(num_frames), int(frame)))
        keys[f] = min(keys[f], value) if f in keys else value

    def ramp(f0, f1, v0, v1):
        """f0→f1 스무스텝 램프 (프레임당 키) — FootIK SmoothStep 방식."""
        span = f1 - f0
        if span <= 0:
            put(f1, v1)
            return
        for f in range(int(f0), int(f1) + 1):
            t = (f - f0) / span
            s = t * t * (3.0 - 2.0 * t)
            put(f, round(v0 + (v1 - v0) * s, 4))

    if merged[0][0] - release_ramp > 0:
        put(0, 1.0)
    for s, e in merged:
        ramp(max(0, s - release_ramp), s, 1.0, 0.0)
        put(e, 0.0)
        ramp(e, e + plant_ramp, 0.0, 1.0)

    frames = sorted(keys)
    return [f / fps for f in frames], [keys[f] for f in frames]


def _build_move_keys(windows, num_frames, fps):
    """플라이트 창 → IK 타깃 이동 커브 (0=이동전 그립, 1=이동후 그립, v5).

    각 창에서 창길이 비례 누적분만큼 스무스텝 상승, 플랜트 구간 홀드.
    창 없으면 상수 0 (Idle류 — 타깃 이동 없음). 프레임 dict 로 중복 차단.
    """
    if not windows:
        return [0.0], [0.0]
    total = float(sum(e - s + 1 for s, e in windows))
    keys = {}

    def put(frame, value):
        keys[max(0, min(int(num_frames), int(frame)))] = round(value, 4)

    put(0, 0.0)
    v0 = 0.0
    for s, e in windows:
        v1 = v0 + (e - s + 1) / total
        span = e - s
        for f in range(int(s), int(e) + 1):
            t = (f - s) / span if span > 0 else 1.0
            sm = t * t * (3.0 - 2.0 * t)
            put(f, v0 + (v1 - v0) * sm)
        v0 = v1
    frames = sorted(keys)
    return [f / fps for f in frames], [keys[f] for f in frames]


def apply(asset_path, overrides=None):
    """overrides: DEFAULTS 키 일부를 덮어쓰는 dict (배치/느린 재그립 애님용).
    에셋에 붙은 모디파이어 인스턴스 값보다 우선한다."""
    try:
        seq = unreal.load_asset(asset_path)
        if seq is None:
            _log("ERROR: load failed " + asset_path)
            return
        num_frames = unreal.AnimationLibrary.get_num_frames(seq)
        duration = unreal.AnimationLibrary.get_sequence_length(seq)
        if duration <= 0 or num_frames <= 0:
            _log("ERROR: empty sequence " + asset_path)
            return
        fps = num_frames / duration
        p = _read_params(seq)
        if overrides:
            p.update(overrides)
        bones = [b for b, _, _ in HANDS] + [PELVIS_BONE]
        positions = _sample_bone_positions(seq, num_frames, duration, bones)

        def _write_curve(curve, times, values):
            # 같은 프레임 키 2개 = SetCurveControlKey 어설션 크래시 — 절대 통과 금지
            fkeys = [int(round(t * fps)) for t in times]
            if len(set(fkeys)) != len(fkeys):
                _log("SKIP %s %s: duplicate frame keys %s" % (seq.get_name(), curve, fkeys))
                return False
            try:
                unreal.AnimationLibrary.remove_curve(seq, curve)
            except Exception:
                pass
            unreal.AnimationLibrary.add_curve(seq, curve)
            unreal.AnimationLibrary.add_float_curve_keys(seq, curve, times, values)
            return True

        for bone, curve, move_curve in HANDS:
            windows, _ = _flight_windows(
                positions[bone], fps,
                float(p["FlightSpeedThreshold"]), int(p["MinFlightFrames"]))
            times, values = _build_keys(
                windows, int(num_frames), fps,
                int(p["PlantRampFrames"]), int(p["ReleaseRampFrames"]))
            if _write_curve(curve, times, values):
                _log("%s <- %s : windows=%s keys=%d" %
                     (seq.get_name(), curve, windows, len(times)))
            # v5: IK 타깃 이동 커브 (0=이동전 그립, 1=이동후 그립)
            mt, mv = _build_move_keys(windows, int(num_frames), fps)
            if _write_curve(move_curve, mt, mv):
                _log("%s <- %s : keys=%d" % (seq.get_name(), move_curve, len(mt)))

        # 펠비스 스프링 엔벨로프 — 프레임당 1키 (고유 프레임 보장)
        pv = _pelvis_spring_values(
            positions[PELVIS_BONE], fps,
            float(p["PelvisMinSpeed"]), int(p["PelvisFallFrames"]))
        pt = [f / fps for f in range(len(pv))]
        try:
            unreal.AnimationLibrary.remove_curve(seq, PELVIS_CURVE)
        except Exception:
            pass
        unreal.AnimationLibrary.add_curve(seq, PELVIS_CURVE)
        unreal.AnimationLibrary.add_float_curve_keys(seq, PELVIS_CURVE, pt, pv)
        _log("%s <- %s : keys=%d peak=%.2f" %
             (seq.get_name(), PELVIS_CURVE, len(pv), max(pv) if pv else 0.0))
    except Exception:
        import traceback
        _log("EXCEPTION\n" + traceback.format_exc())


def revert(asset_path):
    try:
        seq = unreal.load_asset(asset_path)
        if seq is None:
            return
        for curve in ALL_CURVES:
            try:
                unreal.AnimationLibrary.remove_curve(seq, curve)
            except Exception:
                pass
        _log("reverted " + asset_path)
    except Exception:
        import traceback
        _log("EXCEPTION\n" + traceback.format_exc())
