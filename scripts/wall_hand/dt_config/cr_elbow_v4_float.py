# -*- coding: utf-8 -*-
"""ElbowAngle v4: double→float 전환 (레이어 WHElbowRad=float와 타입 일치 — 바인딩 홉 불발 대응).
Tan/Mul을 Float 유닛으로 교체, PoleVector.Y 링크 재구성."""
import unreal, traceback

OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/cr_elbow_v4.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
L = []


def step(s):
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))


try:
    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")

    # 1) 구 double 체인 철거
    for nm in ("ElbTan", "ElbYScale"):
        try:
            step(f"rm {nm} {ctrl.remove_node_by_name(nm)}")
        except Exception as e:
            step(f"rm ERR {nm} {str(e)[:50]}")

    # 2) 변수 타입 전환 double→float
    try:
        ok = bp.change_member_variable_type("ElbowAngle", "float", False, False, "0.0")
        step(f"change type -> {ok}")
    except Exception as e:
        step(f"change type ERR {str(e)[:90]} — remove+add fallback")
        try:
            step(f"rm var {bp.remove_member_variable('ElbowAngle')}")
            step(f"add var {bp.add_member_variable('ElbowAngle', 'float', True, False, '0.0')}")
        except Exception as e2:
            step(f"fallback ERR {str(e2)[:90]}")

    # 3) float 유닛 체인
    TAN = "/Script/RigVM.RigVMFunction_MathFloatTan"
    MUL = "/Script/RigVM.RigVMFunction_MathFloatMul"
    n = ctrl.add_unit_node_from_struct_path(TAN, "Execute", unreal.Vector2D(1200, -260), "ElbTanF")
    step(f"add ElbTanF {n.get_node_path() if n else 'NONE'}")
    n = ctrl.add_unit_node_from_struct_path(MUL, "Execute", unreal.Vector2D(1360, -260), "ElbYScaleF")
    step(f"add ElbYScaleF {n.get_node_path() if n else 'NONE'}")
    step(f"sp B=-50 {ctrl.set_pin_default_value('ElbYScaleF.B', '-50.000000', False)}")
    try:
        step(f"bind {ctrl.bind_pin_to_variable('ElbTanF.Value', 'ElbowAngle', False)}")
    except Exception as e:
        step(f"BIND ERR {str(e)[:70]}")
    step(f"lk tan->mul {ctrl.add_link('ElbTanF.Result', 'ElbYScaleF.A')}")
    for h in ("R", "L"):
        try:
            ok = ctrl.add_link("ElbYScaleF.Result", f"TwoBoneIK_{h}.PoleVector.Y")
            step(f"lk ->Pole{h}.Y {ok}")
        except Exception as e:
            step(f"LK ERR Pole{h}.Y {str(e)[:80]}")

    bp.recompile_vm()
    step("recompile_vm OK")
    step(f"saved {unreal.EditorAssetLibrary.save_asset(DST, only_if_is_dirty=False)}")
except Exception:
    step("FATAL\n" + traceback.format_exc())
