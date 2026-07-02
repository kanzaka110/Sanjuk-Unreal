import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/rebuild3_result.txt"
L=[]
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()
    nodes = {n.get_name(): n for n in g.get_nodes()}
    # 0) Weight 변수 CDO 기본값 0 명시 (프리뷰/초기화 안전)
    try:
        gen = bp.generated_class()
        cdo = unreal.get_default_object(gen)
        cur = cdo.get_editor_property("Weight")
        cdo.set_editor_property("Weight", 0.0)
        L.append(f"Weight CDO default: {cur} -> 0.0")
    except Exception as e:
        L.append("CDO ERR " + str(e)[:120])
    # 1) 노드 재생성
    off_struct = nodes["OffsetRotR"].get_script_struct().get_path_name()
    sel_struct = nodes["SelR"].get_script_struct().get_path_name()
    sr = ctrl.add_unit_node_from_struct_path(off_struct, "Execute", unreal.Vector2D(4608, -400), "SideRotR")
    sl = ctrl.add_unit_node_from_struct_path(off_struct, "Execute", unreal.Vector2D(5104, -400), "SideRotL")
    ssr = ctrl.add_unit_node_from_struct_path(sel_struct, "Execute", unreal.Vector2D(4416, -272), "SelSideR")
    ssl = ctrl.add_unit_node_from_struct_path(sel_struct, "Execute", unreal.Vector2D(4896, -272), "SelSideL")
    L.append("spawned")
    ctrl.set_pin_default_value("SideRotR.Item", '(Type=Bone,Name="hand_r")')
    ctrl.set_pin_default_value("SideRotL.Item", '(Type=Bone,Name="hand_l")')
    ctrl.set_pin_default_value("SideRotR.bPropagateToChildren", "True")
    ctrl.set_pin_default_value("SideRotL.bPropagateToChildren", "True")
    rot = "(Rotation=(X=-0.500000,Y=0.000000,Z=0.000000,W=0.866025),Translation=(X=0.000000,Y=0.000000,Z=0.000000),Scale3D=(X=1.000000,Y=1.000000,Z=1.000000))"
    ctrl.set_pin_default_value("SideRotR.OffsetTransform", rot)
    ctrl.set_pin_default_value("SideRotL.OffsetTransform", rot)
    # ⚠ 안전핀: Weight 핀 자체 디폴트도 0 (링크 유실 churn 시 상시회전 방지)
    ctrl.set_pin_default_value("SideRotR.Weight", "0.0")
    ctrl.set_pin_default_value("SideRotL.Weight", "0.0")
    ctrl.set_pin_default_value("SelSideR.IfFalse", "0.0")
    ctrl.set_pin_default_value("SelSideL.IfTrue", "0.0")
    L.append("defaults set (Weight pin 0 안전핀)")
    ctrl.add_link("VariableNode_7.Value", "SelSideR.Condition")
    ctrl.add_link("VariableNode_8.Value", "SelSideL.Condition")
    ctrl.add_link("VariableNode_3.Value", "SelSideR.IfTrue")
    ctrl.add_link("VariableNode_4.Value", "SelSideL.IfFalse")
    ctrl.add_link("SelSideR.Result", "SideRotR.Weight")
    ctrl.add_link("SelSideL.Result", "SideRotL.Weight")
    ctrl.add_link("OffsetRotL.ExecutePin", "SideRotR.ExecutePin")
    ctrl.add_link("SideRotR.ExecutePin", "SideRotL.ExecutePin")
    L.append("links ok")
    bp.recompile_vm(); bp.recompile_vm_if_required()
    ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"save={ok}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
