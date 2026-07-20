# AM_SBLedgeIK 인스턴스 중복 제거 (에디터 py 전용)
# 원인: animation_query("apply_anim_modifier", persist=True) 는 호출할 때마다 스택에 인스턴스를 **추가**한다.
#       (갱신 아님) → 반복 적용 시 동일 모디파이어가 N개 쌓이고, 커브는 마지막 것이 덮어써 혼선 발생
# 처방: 마지막 인스턴스(=최신 값)만 남기고 나머지 제거. 다른 클래스 모디파이어는 보존.
import unreal, json, traceback

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/dedupe_report.json"
DIR = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing"
rep = {"fixed": {}, "ok": 0, "error": {}}
dirty = []

assets = unreal.EditorAssetLibrary.list_assets(DIR, recursive=True, include_folder=False)
if not assets:   # 레지스트리 열거 실패 시 파생 목록 폴백
    assets = [DIR + "/" + n for n in json.load(open("C:/Users/SHIFTUP/AppData/Local/Temp/claude/derived_windows.json")).keys()]
rep["scanned"] = len(assets)
for path in assets:
    p = path.split(".")[0]
    nm = p.split("/")[-1]
    try:
        seq = unreal.load_asset(p)
        if not isinstance(seq, unreal.AnimSequence):
            continue
        for a in (seq.get_editor_property("asset_user_data") or []):
            if not (a and "AnimationModifiers" in str(a.get_class().get_name())):
                continue
            insts = list(a.get_editor_property("animation_modifier_instances") or [])
            ledge = [i for i in insts if i and "SBLedge" in str(i.get_class().get_name())]
            if len(ledge) <= 1:
                rep["ok"] += 1
                continue
            keep = ledge[-1]                       # 최신 적용본 유지
            others = [i for i in insts if i and "SBLedge" not in str(i.get_class().get_name())]
            a.set_editor_property("animation_modifier_instances", others + [keep])
            rep["fixed"][nm] = len(ledge)
            seq.modify()
            dirty.append(seq.get_outermost())
    except Exception:
        rep["error"][nm] = traceback.format_exc()[-150:]

if dirty:
    try:
        rep["saved"] = bool(unreal.EditorLoadingAndSavingUtils.save_packages(dirty, only_dirty=False))
    except Exception:
        rep["save_error"] = traceback.format_exc()[-200:]
rep["fixed_count"] = len(rep["fixed"])
with open(OUT, "w") as f:
    json.dump(rep, f, indent=1, ensure_ascii=False)
print("DEDUPE_DONE fixed=%d ok=%d err=%d" % (len(rep["fixed"]), rep["ok"], len(rep["error"])))
