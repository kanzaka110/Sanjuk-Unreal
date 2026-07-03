import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/stablerot_r_result.txt"
L=[]
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()
    nodes = {n.get_name(): n for n in g.get_nodes()}
    # 현재 TwoBoneIK_R.Effector.Rotation 소스
    tb = nodes["TwoBoneIK_R"]; src = None
    for p in tb.get_pins():
        if p.get_name()=="Effector":
            for sp in p.get_sub_pins():
                if sp.get_name()=="Rotation":
                    for s in sp.get_linked_source_pins(): src = s.get_pin_path()
    L.append(f"현 소스: {src}")
    qmul = ctrl.add_unit_node_from_struct_path("/Script/RigVM.RigVMFunction_MathQuaternionMul", "Execute", unreal.Vector2D(520, 980), "QMulR")
    ctrl.set_pin_default_value("QMulR.B", "(X=0.487681,Y=-0.512023,Z=-0.487681,W=-0.512023)")
    ctrl.add_link("GetRootTf.Transform.Rotation", "QMulR.A")
    if src:
        ctrl.break_link(src, "TwoBoneIK_R.Effector.Rotation")
    ctrl.add_link("QMulR.Result", "TwoBoneIK_R.Effector.Rotation")
    L.append("effector wired")
    # PalmAim(우) 비활성
    pa = nodes["PalmAim"]
    for p in pa.get_pins():
        if p.get_name()=="Weight":
            for s in p.get_linked_source_pins():
                ctrl.break_link(s.get_pin_path(), "PalmAim.Weight")
                L.append(f"break {s.get_pin_path()}")
    ctrl.set_pin_default_value("PalmAim.Weight", "0.0")
    L.append("PalmAim.Weight=0")
    bp.recompile_vm(); bp.recompile_vm_if_required()
    ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"save={ok}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
