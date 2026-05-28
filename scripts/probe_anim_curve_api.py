"""
AnimSequence curve API 탐색 — UE 5.7 SB2 빌드 기준.
실행 후 출력으로 정확한 메서드명 확인해서 본 스크립트(rate_limit_footik_curves.py) 수정.

실행: PIE 종료 후
  exec(open(r"C:\Dev\Sanjuk-Unreal\scripts\probe_anim_curve_api.py", encoding="utf-8").read(), {"__name__": "__main__"})
"""
import unreal

TARGET = "/Game/Art/Character/PC/PC_01/Animation/Body/Run/P_Player_Run_Stop_F_Lfoot"
CURVE = "DisableFootIK_L"


def dump_methods(obj, label, keywords=("curve", "data_model", "controller", "key")):
    names = sorted(dir(obj))
    matched = [n for n in names if any(k in n.lower() for k in keywords) and not n.startswith("__")]
    unreal.log(f"--- {label} 매칭 메서드 ({len(matched)}개) ---")
    for n in matched:
        unreal.log(f"    {n}")


def main():
    seq = unreal.load_asset(TARGET)
    unreal.log(f"[OBJ] {type(seq).__name__}")

    dump_methods(seq, "AnimSequence 인스턴스")

    # AnimationLibrary static 메서드 탐색
    dump_methods(unreal.AnimationLibrary, "AnimationLibrary static")

    # 흔한 API 후보들 시도
    candidates = [
        ("seq.get_data_model_interface()", lambda: seq.get_data_model_interface()),
        ("seq.get_controller()", lambda: seq.get_controller()),
        ("seq.data_model", lambda: getattr(seq, "data_model", None)),
        ("seq.controller", lambda: getattr(seq, "controller", None)),
        ("unreal.AnimationLibrary.get_float_curve_keys(seq, CURVE)",
         lambda: unreal.AnimationLibrary.get_float_curve_keys(seq, CURVE)),
        ("unreal.AnimationLibrary.get_float_keys(seq, CURVE)",
         lambda: unreal.AnimationLibrary.get_float_keys(seq, CURVE)),
        ("unreal.AnimationLibrary.does_curve_exist(seq, CURVE, RCT_FLOAT)",
         lambda: unreal.AnimationLibrary.does_curve_exist(
             seq, CURVE, unreal.RawCurveTrackTypes.RCT_FLOAT)),
    ]
    unreal.log("--- API 후보 시도 ---")
    for desc, fn in candidates:
        try:
            r = fn()
            unreal.log(f"  [OK] {desc} -> {type(r).__name__} : {str(r)[:120]}")
            if r is not None and hasattr(r, "__class__") and not isinstance(r, (bool, int, float, str)):
                dump_methods(r, f"  └─ return 객체 ({type(r).__name__})")
        except Exception as e:
            unreal.log(f"  [FAIL] {desc} -> {type(e).__name__}: {str(e)[:120]}")


if __name__ == "__main__":
    main()
