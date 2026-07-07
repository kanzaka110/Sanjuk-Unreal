# -*- coding: utf-8 -*-
"""ElbowAngle 최종판 v3 (사용자 지시: Basic IK 폴벡터 Y 구동).
진범 해명: PoleVector(Direction)는 크기 민감 — 단위벡터(크기1)는 1cm급 무효, 원본 스케일=50.
설계: PoleVector = (∓50, -50*tan(ElbowAngle), 1). 0rad=현행 정확 등가, +뒤/-앞.
Test C/D 원복 포함: 폴 X/Z 원상, SecondaryAxisWeight=1.0, 구 Elb* 노드 철거."""
import unreal, traceback

OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dt_config/cr_elbow_v3.txt"
DST = "/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
L = []


def step(s):
    L.append(str(s))
    open(OUT, "w", encoding="utf-8").write("\n".join(L))


try:
    bp = unreal.load_asset(DST)
    ctrl = bp.get_controller_by_name("RigVMModel")

    # 1) Test C/D 원복 + 구 체인 철거
    for h in ("R", "L"):
        ok = ctrl.set_pin_default_value(f"TwoBoneIK_{h}.SecondaryAxisWeight", "1.000000", False)
        step(f"restore SAW {h} {ok}")
    for nm in ("ElbDirR", "ElbDirL", "ElbNeg", "ElbCos", "ElbSin"):
        try:
            ok = ctrl.remove_node_by_name(nm)
            step(f"rm {nm} {ok}")
        except Exception as e:
            step(f"rm ERR {nm} {str(e)[:50]}")
    ctrl.set_pin_default_value("TwoBoneIK_R.PoleVector", "(X=-50.000000,Y=0.000000,Z=1.000000)", False)
    ctrl.set_pin_default_value("TwoBoneIK_L.PoleVector", "(X=50.000000,Y=0.000000,Z=1.000000)", False)
    step("pole X/Z restored")

    # 2) 신규 체인: Tan(ElbowAngle) × (-50) → PoleVector.Y (양손 서브핀 링크)
    TAN = "/Script/RigVM.RigVMFunction_MathDoubleTan"
    MUL = "/Script/RigVM.RigVMFunction_MathDoubleMul"
    n = ctrl.add_unit_node_from_struct_path(TAN, "Execute", unreal.Vector2D(1200, -260), "ElbTan")
    step(f"add ElbTan {n.get_node_path() if n else 'NONE'}")
    n = ctrl.add_unit_node_from_struct_path(MUL, "Execute", unreal.Vector2D(1360, -260), "ElbYScale")
    step(f"add ElbYScale {n.get_node_path() if n else 'NONE'}")
    ok = ctrl.set_pin_default_value("ElbYScale.B", "-50.000000", False)
    step(f"sp ElbYScale.B=-50 {ok}")
    try:
        ok = ctrl.bind_pin_to_variable("ElbTan.Value", "ElbowAngle", False)
        step(f"bind ElbTan.Value<-ElbowAngle {ok}")
    except Exception as e:
        step(f"BIND ERR {str(e)[:70]}")
    ok = ctrl.add_link("ElbTan.Result", "ElbYScale.A")
    step(f"lk tan->scale {ok}")
    for h in ("R", "L"):
        try:
            ok = ctrl.add_link("ElbYScale.Result", f"TwoBoneIK_{h}.PoleVector.Y")
            step(f"lk ->Pole{h}.Y {ok}")
        except Exception as e:
            step(f"LK ERR Pole{h}.Y {str(e)[:60]}")

    bp.recompile_vm()
    step("recompile_vm OK")
    ok = unreal.EditorAssetLibrary.save_asset(DST, only_if_is_dirty=False)
    step(f"saved {ok}")
except Exception:
    step("FATAL\n" + traceback.format_exc())
