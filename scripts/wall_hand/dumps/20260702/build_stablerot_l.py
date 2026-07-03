import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/stablerot_result.txt"
L=[]
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()
    nodes = {n.get_name(): n for n in g.get_nodes()}
    # 현재 TwoBoneIK_L.Effector.Rotation 소스 확인
    tb = nodes["TwoBoneIK_L"]
    src_path = None
    def find_pin(n, path):
        for p in n.get_pins():
            if p.get_name()=="Effector":
                for sp in p.get_sub_pins():
                    if sp.get_name()=="Rotation":
                        return sp
        return None
    rp = find_pin(tb, "Rotation")
    for s in rp.get_linked_source_pins():
        src_path = s.get_pin_path()
    L.append(f"현 Effector.Rotation ← {src_path}")
    # GetTransform 구조체 경로 (GetHand_L에서 취득)
    gt_struct = nodes["GetHand_L"].get_script_struct().get_path_name()
    L.append(f"GetTransform struct={gt_struct}")
    # root GetTransform 노드
    groot = ctrl.add_unit_node_from_struct_path(gt_struct, "Execute", unreal.Vector2D(300, 900), "GetRootTf")
    ctrl.set_pin_default_value("GetRootTf.Item", '(Type=Bone,Name="root")')
    L.append("GetRootTf ok")
    # 쿼터니언 곱 유닛
    qmul = None
    for sp_try in ("/Script/RigVM.RigVMFunction_MathQuaternionMul",
                   "/Script/ControlRig.RigUnit_MathQuaternionMul"):
        try:
            qmul = ctrl.add_unit_node_from_struct_path(sp_try, "Execute", unreal.Vector2D(520, 900), "QMulL")
            L.append(f"QMulL ok ({sp_try})"); break
        except Exception as e:
            L.append(f"{sp_try} 실패: {str(e)[:60]}")
    if qmul:
        ctrl.set_pin_default_value("QMulL.B", "(X=0.507812,Y=-0.492064,Z=0.507812,W=0.492064)")
        ctrl.add_link("GetRootTf.Transform.Rotation", "QMulL.A")
        if src_path:
            ctrl.break_link(src_path, "TwoBoneIK_L.Effector.Rotation")
        ctrl.add_link("QMulL.Result", "TwoBoneIK_L.Effector.Rotation")
        L.append("wired")
        bp.recompile_vm(); bp.recompile_vm_if_required()
        ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
        L.append(f"save={ok}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
