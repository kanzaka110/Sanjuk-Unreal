import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/slerp_result.txt"
L=[]
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()
    nodes = {n.get_name(): n for n in g.get_nodes()}
    # 현 QSel 디폴트(측면 상수) 회수
    def pin_def(node, pin):
        for p in nodes[node].get_pins():
            if p.get_name()==pin: return p.get_default_value()
    sideR = pin_def("QSelR","IfFalse"); sideL = pin_def("QSelL","IfFalse")
    L.append(f"sideR={sideR}")
    L.append(f"sideL={sideL}")
    # Slerp 유닛 스폰
    sl_struct = None
    for sp in ("/Script/RigVM.RigVMFunction_MathQuaternionSlerp",):
        try:
            ctrl.add_unit_node_from_struct_path(sp, "Execute", unreal.Vector2D(700, 1060), "QLerpR")
            sl_struct = sp; break
        except Exception as e: L.append(f"{sp} 실패 {str(e)[:70]}")
    if not sl_struct: raise RuntimeError("Slerp 유닛 없음")
    ctrl.add_unit_node_from_struct_path(sl_struct, "Execute", unreal.Vector2D(700, 1160), "QLerpL")
    L.append("slerp 스폰 ok")
    ctrl.set_pin_default_value("QLerpR.A", sideR)
    ctrl.set_pin_default_value("QLerpL.A", sideL)
    ctrl.add_link("QMulR.Result", "QLerpR.B")
    ctrl.add_link("QMulL.Result", "QLerpL.B")
    # T ← Weight 변수 (bind — 안전 검증된 API)
    ctrl.bind_pin_to_variable("QLerpR.T", "Weight")
    ctrl.bind_pin_to_variable("QLerpL.T", "Weight")
    L.append("A/B/T ok")
    # Effector 교체 + QSel 제거
    for side in ("R","L"):
        ctrl.break_link(f"QSel{side}.Result", f"TwoBoneIK_{side}.Effector.Rotation")
        ctrl.add_link(f"QLerp{side}.Result", f"TwoBoneIK_{side}.Effector.Rotation")
        ctrl.remove_node_by_name(f"QSel{side}")
        L.append(f"{side} 교체 ok")
    bp.recompile_vm(); bp.recompile_vm_if_required()
    ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"save={ok}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
