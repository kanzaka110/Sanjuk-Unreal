# LedgeClimbing 전 시퀀스 AM_SBLedgeIK 인스턴스 파라미터 일괄 세팅 (에디터 py 전용)
# 입력: ledge_windows.json (커브 역산 창) — 커브가 ground truth, 인스턴스 값을 커브에 동기화
#  - Hand/FootMove* = 커브 램프 창 (창 없으면 미변경)
#  - PelvisSpring* = 이동계 휴리스틱: Start=max(HandEnd)+0.05, Full=+0.15, HoldEnd=+0.50, End=+0.85
#    (⚠ 가설 — Short 실측 템플릿 0.40/0.55/0.90/1.25 와 ±0.02 정합. 비이동계는 미변경)
# 출력: mod_apply_report.json (per-anim 적용값/스킵/실패)
import unreal, json

WIN = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/ledge_windows.json"
OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/mod_apply_report.json"
DIR = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing/"
wins = json.load(open(WIN))
report = {"set": {}, "skip": [], "no_instance": [], "save_fail": [], "error": {}}
dirty = []

for nm, w in sorted(wins.items()):
    try:
        seq = unreal.load_asset(DIR + nm)
        if seq is None:
            report["error"][nm] = "load fail"
            continue
        inst = None
        for a in (seq.get_editor_property("asset_user_data") or []):
            if a and "AnimationModifiers" in str(a.get_class().get_name()):
                for i in (a.get_editor_property("animation_modifier_instances") or []):
                    if i and "SBLedge" in str(i.get_class().get_name()):
                        inst = i
        if inst is None:
            report["no_instance"].append(nm)
            continue
        hl, hr = w.get("hand_l"), w.get("hand_r")
        fl, fr = w.get("foot_l"), w.get("foot_r")
        if not hl and not hr:
            report["skip"].append(nm)
            continue
        vals = {}
        if hl:
            vals["HandMoveStartL"], vals["HandMoveEndL"] = hl
        if hr:
            vals["HandMoveStartR"], vals["HandMoveEndR"] = hr
        if fl:
            vals["FootMoveStartL"], vals["FootMoveEndL"] = fl
        if fr:
            vals["FootMoveStartR"], vals["FootMoveEndR"] = fr
        ends = [x[1] for x in (hl, hr) if x]
        ps = round(max(ends) + 0.05, 3)
        vals["PelvisSpringStart"] = ps
        vals["PelvisSpringFull"] = round(ps + 0.15, 3)
        vals["PelvisSpringHoldEnd"] = round(ps + 0.50, 3)
        vals["PelvisSpringEnd"] = round(ps + 0.85, 3)
        for k, v in vals.items():
            inst.set_editor_property(k, float(v))
        seq.modify()
        dirty.append(seq)
        report["set"][nm] = vals
    except Exception as e:
        report["error"][nm] = repr(e)[:150]

# 저장 (배치)
pkgs = [s.get_outermost() for s in dirty]
ok = True
try:
    ok = unreal.EditorLoadingAndSavingUtils.save_packages(pkgs, only_dirty=False)
except Exception as e:
    report["save_fail"].append(repr(e)[:200])
report["saved_count"] = len(pkgs) if ok else 0

with open(OUT, "w") as fp:
    json.dump(report, fp, indent=1)
print("MOD_APPLY_DONE set=%d skip=%d noinst=%d err=%d" %
      (len(report["set"]), len(report["skip"]), len(report["no_instance"]), len(report["error"])))
