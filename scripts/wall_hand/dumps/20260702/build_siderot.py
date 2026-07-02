import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/build_siderot_result.txt"
L = []
def w(s): L.append(str(s))
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()
    nodes = {n.get_name(): n for n in g.get_nodes()}
    # 기존 노드에서 struct 경로 취득
    off_struct = nodes["OffsetRotR"].get_script_struct().get_path_name()
    sel_struct = nodes["SelR"].get_script_struct().get_path_name()
    w(f"offset struct={off_struct}")
    w(f"select struct={sel_struct}")
    # OffsetRotL 다음 exec 타겟 확인
    tail = None
    for p in nodes["OffsetRotL"].get_pins():
        if p.get_name() == "ExecutePin":
            tgts = p.get_linked_target_pins()
            if tgts: tail = tgts[0].get_pin_path()
    w(f"OffsetRotL exec tail={tail}")
    # 노드 생성
    sr = ctrl.add_unit_node_from_struct_path(off_struct, "Execute", unreal.Vector2D(2200, 300), "SideRotR")
    sl = ctrl.add_unit_node_from_struct_path(off_struct, "Execute", unreal.Vector2D(2400, 300), "SideRotL")
    ssr = ctrl.add_unit_node_from_struct_path(sel_struct, "Execute", unreal.Vector2D(2000, 450), "SelSideR")
    ssl = ctrl.add_unit_node_from_struct_path(sel_struct, "Execute", unreal.Vector2D(2000, 550), "SelSideL")
    w(f"spawned: {[x.get_name() for x in (sr,sl,ssr,ssl)]}")
    # 핀 디폴트
    ctrl.set_pin_default_value("SideRotR.Item", '(Type=Bone,Name="hand_r")')
    ctrl.set_pin_default_value("SideRotL.Item", '(Type=Bone,Name="hand_l")')
    ctrl.set_pin_default_value("SideRotR.bPropagateToChildren", "True")
    ctrl.set_pin_default_value("SideRotL.bPropagateToChildren", "True")
    ident = "(Rotation=(X=0.000000,Y=0.000000,Z=0.000000,W=1.000000),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))"
    ctrl.set_pin_default_value("SideRotR.OffsetTransform", ident)
    ctrl.set_pin_default_value("SideRotL.OffsetTransform", ident)
    ctrl.set_pin_default_value("SelSideR.IfFalse", "0.0")
    ctrl.set_pin_default_value("SelSideL.IfTrue", "0.0")
    w("defaults set")
    # 값 배선: bRight(VariableNode_7/8) → Condition, Weight(VariableNode_3/4) → IfTrue/IfFalse
    ctrl.add_link("VariableNode_7.Value", "SelSideR.Condition")
    ctrl.add_link("VariableNode_8.Value", "SelSideL.Condition")
    ctrl.add_link("VariableNode_3.Value", "SelSideR.IfTrue")
    ctrl.add_link("VariableNode_4.Value", "SelSideL.IfFalse")
    ctrl.add_link("SelSideR.Result", "SideRotR.Weight")
    ctrl.add_link("SelSideL.Result", "SideRotL.Weight")
    w("value links ok")
    # exec: OffsetRotL → SideRotR → SideRotL (기존 tail 있으면 이어붙임)
    if tail:
        ctrl.break_link("OffsetRotL.ExecutePin", tail)
    ctrl.add_link("OffsetRotL.ExecutePin", "SideRotR.ExecutePin")
    ctrl.add_link("SideRotR.ExecutePin", "SideRotL.ExecutePin")
    if tail:
        ctrl.add_link("SideRotL.ExecutePin", tail)
    w("exec chained")
    bp.recompile_vm(); bp.recompile_vm_if_required()
    ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    w(f"save={ok}")
except Exception:
    w(traceback.format_exc())
open(OUT, "w", encoding="utf-8").write("\n".join(L))
