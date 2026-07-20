# 실측 스윙창(swing_windows.json) → AM_SBLedgeIK 인스턴스 파라미터 일괄 적용 (에디터 py 전용)
#  - Hand/FootMove* = 본 속도 실측 스윙창 (애님별 고유값)
#  - PelvisSpring*  = base(=max 손 플랜트) + 0.05/0.20/0.55/0.90  ⚠ 가설 (검증값 델타 유지)
#  - 이탈/정지 계열(ToLadder/End_/Idle)은 스킵 — 모디파이어가 이탈·정지 커브로 분류 처리
#  - PRESERVE = 유저 PIE 검증값 유지 (측정창과 불일치, 검증값 우선)
import unreal, json, traceback

WIN = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/derived_windows.json"
OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/measured_apply_report.json"
DIR = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/"
PRESERVE = {"P_Player_Ledge_Move_ShortL_Wallless", "P_Player_Ledge_Move_ShortR_Wallless"}
SKIP_TOKENS = ("ToLadder", "_End_", "_Idle")
wins = json.load(open(WIN))
rep = {"set": {}, "skip_class": [], "skip_nowindow": [], "preserved": [], "no_instance": [], "error": {}}
dirty = []


def inst_of(seq):
    for a in (seq.get_editor_property("asset_user_data") or []):
        if a and "AnimationModifiers" in str(a.get_class().get_name()):
            for i in (a.get_editor_property("animation_modifier_instances") or []):
                if i and "SBLedge" in str(i.get_class().get_name()):
                    return i
    return None


for nm, w in sorted(wins.items()):
    try:
        if nm in PRESERVE:
            rep["preserved"].append(nm)
            continue
        if any(t in nm for t in SKIP_TOKENS):
            rep["skip_class"].append(nm)
            continue
        hl, hr = w.get("hand_l"), w.get("hand_r")
        if not hl and not hr:
            rep["skip_nowindow"].append(nm)
            continue
        seq = unreal.load_asset(DIR + nm)
        inst = inst_of(seq)
        if inst is None:
            rep["no_instance"].append(nm)
            continue
        dur = float(w.get("dur") or 0.0)
        vals = {}
        if hl:
            vals["HandMoveStartL"], vals["HandMoveEndL"] = hl
        if hr:
            vals["HandMoveStartR"], vals["HandMoveEndR"] = hr
        fl, fr = w.get("ball_l"), w.get("ball_r")
        if fl:
            vals["FootMoveStartL"], vals["FootMoveEndL"] = fl
        if fr:
            vals["FootMoveStartR"], vals["FootMoveEndR"] = fr
        # 2차 릴리즈 창 (v10) — 없으면 0/0 = 비활성
        for src, pre in (("hand_l_2", "HandMove2"), ("hand_r_2", "HandMove2"),
                         ("ball_l_2", "FootMove2"), ("ball_r_2", "FootMove2")):
            side = "L" if src.split("_")[1] == "l" else "R"
            w2 = w.get(src)
            vals[pre + "Start" + side] = round(w2[0], 3) if w2 else 0.0
            vals[pre + "End" + side] = round(min(w2[1], dur), 3) if w2 else 0.0
        base = max([x[1] for x in (hl, hr) if x])
        for k, d in (("PelvisSpringStart", 0.05), ("PelvisSpringFull", 0.20),
                     ("PelvisSpringHoldEnd", 0.55), ("PelvisSpringEnd", 0.90)):
            vals[k] = round(min(base + d, dur if dur else base + d), 3)
        for k, v in vals.items():
            inst.set_editor_property(k, float(v))
        seq.modify()
        dirty.append(seq.get_outermost())
        rep["set"][nm] = vals
    except Exception:
        rep["error"][nm] = traceback.format_exc()[-200:]

if dirty:
    try:
        rep["saved"] = bool(unreal.EditorLoadingAndSavingUtils.save_packages(dirty, only_dirty=False))
    except Exception:
        rep["save_error"] = traceback.format_exc()[-200:]
rep["counts"] = {k: len(v) for k, v in rep.items() if isinstance(v, (list, dict))}
with open(OUT, "w") as f:
    json.dump(rep, f, indent=1)
print("MEASURED_APPLY_DONE set=%d" % len(rep["set"]))
