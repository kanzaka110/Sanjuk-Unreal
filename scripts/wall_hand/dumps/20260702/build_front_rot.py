import unreal, traceback, math
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/front_rot_result.txt"
L=[]
try:
    # 정면 오프셋 유도: 측면 오프셋에 root-로컬 yaw ∓90 프리멀티
    offR = unreal.Quat(0.487681,-0.512023,-0.487681,-0.512023)
    offL = unreal.Quat(0.507812,-0.492064,0.507812,0.492064)
    s = math.sin(math.radians(-45)); c = math.cos(math.radians(45))
    qzN = unreal.Quat(0,0,s,c)     # yaw -90
    qzP = unreal.Quat(0,0,-s,c)    # yaw +90
    offRF = qzN.multiply(offR)
    offLF = qzP.multiply(offL)
    L.append(f"offR_front=({offRF.x:.6f},{offRF.y:.6f},{offRF.z:.6f},{offRF.w:.6f})")
    L.append(f"offL_front=({offLF.x:.6f},{offLF.y:.6f},{offLF.z:.6f},{offLF.w:.6f})")

    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    # 쿼터니언 SelectBool 유닛 스폰
    qsel_struct = None
    for sp in ("/Script/RigVM.RigVMFunction_MathQuaternionSelectBool",):
        try:
            ctrl.add_unit_node_from_struct_path(sp, "Execute", unreal.Vector2D(380, 1060), "QSelR")
            qsel_struct = sp; break
        except Exception as e:
            L.append(f"{sp} 실패: {str(e)[:70]}")
    if not qsel_struct:
        raise RuntimeError("Quat SelectBool 유닛 없음")
    ctrl.add_unit_node_from_struct_path(qsel_struct, "Execute", unreal.Vector2D(380, 1160), "QSelL")
    L.append("QSel 스폰 ok")
    def qs(q): return f"(X={q.x:.6f},Y={q.y:.6f},Z={q.z:.6f},W={q.w:.6f})"
    ctrl.set_pin_default_value("QSelR.IfTrue", qs(offRF))
    ctrl.set_pin_default_value("QSelR.IfFalse", qs(offR))
    ctrl.set_pin_default_value("QSelL.IfTrue", qs(offLF))
    ctrl.set_pin_default_value("QSelL.IfFalse", qs(offL))
    # Condition ← bWallHandFront (기존 게터 VariableNode_9 재사용)
    ctrl.add_link("VariableNode_9.Value", "QSelR.Condition")
    ctrl.add_link("VariableNode_9.Value", "QSelL.Condition")
    # QMul.B ← 선택 결과
    ctrl.add_link("QSelR.Result", "QMulR.B")
    ctrl.add_link("QSelL.Result", "QMulL.B")
    L.append("wired")
    bp.recompile_vm(); bp.recompile_vm_if_required()
    ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"save={ok}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
