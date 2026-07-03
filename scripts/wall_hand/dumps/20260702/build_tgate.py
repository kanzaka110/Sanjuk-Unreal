import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/tgate_result.txt"
L=[]
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()
    nodes = {n.get_name(): n for n in g.get_nodes()}
    remap_s = nodes["PalmReleaseRemap"].get_script_struct().get_path_name()  # MathFloatRemap
    mul_s   = nodes["MulK"].get_script_struct().get_path_name()             # MathFloatMul
    # 타겟 분리 길이: Dot(WallD, WallDir[정규화]) = 길이
    dot_s = "/Script/RigVM.RigVMFunction_MathVectorDot"
    ctrl.add_unit_node_from_struct_path(dot_s, "Execute", unreal.Vector2D(480, -560), "WallLen")
    ctrl.add_link("WallD.Result", "WallLen.A")
    ctrl.add_link("WallDir.Result", "WallLen.B")
    # 분리도 램프 5→25cm = 0→1
    ctrl.add_unit_node_from_struct_path(remap_s, "Execute", unreal.Vector2D(640, -560), "TGate")
    ctrl.add_link("WallLen.Result", "TGate.Value")
    ctrl.set_pin_default_value("TGate.SourceMinimum", "5.0")
    ctrl.set_pin_default_value("TGate.SourceMaximum", "25.0")
    ctrl.set_pin_default_value("TGate.TargetMinimum", "0.0")
    ctrl.set_pin_default_value("TGate.TargetMaximum", "1.0")
    ctrl.set_pin_default_value("TGate.bClamp", "true")
    # T = WHFrontBlend(Weight var) × TGate
    for side in ("R","L"):
        nm=f"TMul{side}"
        ctrl.add_unit_node_from_struct_path(mul_s, "Execute", unreal.Vector2D(820, 1060 if side=="R" else 1160), nm)
        try: ctrl.unbind_pin_from_variable(f"QLerp{side}.T")
        except Exception as e: L.append(f"unbind {side}: {str(e)[:60]}")
        ctrl.bind_pin_to_variable(f"{nm}.A", "Weight")
        ctrl.add_link("TGate.Result", f"{nm}.B")
        ctrl.add_link(f"{nm}.Result", f"QLerp{side}.T")
        L.append(f"{side} T게이트 ok")
    bp.recompile_vm(); bp.recompile_vm_if_required()
    ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"save={ok}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
