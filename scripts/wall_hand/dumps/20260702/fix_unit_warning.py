import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/unit_warn_result.txt"
L=[]
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()
    nodes = {n.get_name(): n for n in g.get_nodes()}
    add_struct = nodes["PalmReachSum"].get_script_struct().get_path_name()  # MathVectorAdd
    ctrl.add_unit_node_from_struct_path(add_struct, "Execute", unreal.Vector2D(260, -560), "WallDBias")
    ctrl.set_pin_default_value("WallDBias.B", "(X=0.001000,Y=0.000000,Z=0.000000)")
    ctrl.break_link("WallD.Result", "WallDir.Value")
    ctrl.add_link("WallD.Result", "WallDBias.A")
    ctrl.add_link("WallDBias.Result", "WallDir.Value")
    L.append("bias 삽입 ok")
    bp.recompile_vm(); bp.recompile_vm_if_required()
    ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"save={ok}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
