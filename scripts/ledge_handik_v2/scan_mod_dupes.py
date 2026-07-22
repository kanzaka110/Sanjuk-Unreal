# AM_SBLedgeIK 중복 인스턴스 정밀 스캔 (read-only, 에디터 py 전용)
# 목적: 2개+ 쌓인 애님에서 인스턴스별 파라미터를 나란히 덤프 → 어느 쪽이 정상값인지 판정 후 dedupe 정책 결정
# 실행: py "H:/내 드라이브/Claude/Sanjuk-Unreal/scripts/ledge_handik_v2/scan_mod_dupes.py"
import unreal, json, traceback

OUT = "C:/Users/SHIFTUP/AppData/Local/Temp/claude/mod_dupes_scan.json"
DIR = "/Game/Art/Character/PC/PC_01/Animation/Body/LedgeClimbing"
KEYS = ["HandMoveStartL", "HandMoveEndL", "HandMoveStartR", "HandMoveEndR",
        "FootMoveStartL", "FootMoveEndL", "FootMoveStartR", "FootMoveEndR",
        "ReleaseRampTime", "PlantRampTime",
        "PelvisSpringStart", "PelvisSpringFull", "PelvisSpringHoldEnd", "PelvisSpringEnd"]
rep = {"dupes": {}, "singles": 0, "none": 0, "errors": {}}

ar = unreal.AssetRegistryHelpers.get_asset_registry()
paths = sorted({str(a.package_name) for a in ar.get_assets_by_path(DIR, recursive=True)
                if str(a.package_name).split("/")[-1].startswith("P_Player_Ledge")})
for p in paths:
    nm = p.split("/")[-1]
    try:
        seq = unreal.load_asset(p)
        if not isinstance(seq, unreal.AnimSequence):
            continue
        ledge = []
        for a in (seq.get_editor_property("asset_user_data") or []):
            if not (a and "AnimationModifiers" in str(a.get_class().get_name())):
                continue
            for i in (a.get_editor_property("animation_modifier_instances") or []):
                if i and "SBLedge" in str(i.get_class().get_name()):
                    ledge.append(i)
        if not ledge:
            rep["none"] += 1
            continue
        if len(ledge) == 1:
            rep["singles"] += 1
            continue
        entry = []
        for idx, inst in enumerate(ledge):
            vals = {}
            for k in KEYS:
                try:
                    v = inst.get_editor_property(k)
                    vals[k] = round(float(v), 4)
                except Exception:
                    pass
            entry.append({"idx": idx, "class": str(inst.get_class().get_name()), "params": vals})
        rep["dupes"][nm] = entry
    except Exception:
        rep["errors"][nm] = traceback.format_exc()[-120:]

json.dump(rep, open(OUT, "w"), indent=1)
print("SCAN DONE: dupes=%d singles=%d none=%d err=%d -> %s" % (
    len(rep["dupes"]), rep["singles"], rep["none"], len(rep["errors"]), OUT))
