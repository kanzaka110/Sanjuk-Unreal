# -*- coding: utf-8 -*-
"""판별 실험: ElbSin/ElbCos의 변수 바인딩 해제 + Value 리터럴 0.803(46°) 직접 세팅.
→ 팔꿈치 움직이면 폴 링크는 정상 = 범인은 변수 바인딩 층.
→ 안 움직이면 링크→PoleVector 평가 자체가 죽은 것."""
import unreal, traceback

OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/elbow_isolate_literal.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
L = []


def step(s):
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))


try:
    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")
    for pin in ("ElbSin.Value", "ElbCos.Value"):
        try:
            ok = ctrl.unbind_pin_from_variable(pin)
            step(f"unbind {pin} -> {ok}")
        except Exception as e:
            step(f"unbind ERR {pin} {str(e)[:70]}")
    for pin in ("ElbSin.Value", "ElbCos.Value"):
        ok = ctrl.set_pin_default_value(pin, "0.803000", False)
        step(f"sp {pin}=0.803 -> {ok}")
    try:
        bp.recompile_vm()
        step("recompile_vm OK")
    except Exception as e:
        step(f"recompile FAIL {str(e)[:80]}")
    ok = unreal.EditorAssetLibrary.save_asset(DST, only_if_is_dirty=False)
    step(f"saved {ok}")
except Exception:
    step("FATAL\n" + traceback.format_exc())
