import unreal, traceback
OUT = r"C:/Dev/Sanjuk-Unreal/scripts/wall_hand/dumps/20260702/cleanup_result.txt"
L=[]
try:
    bp = unreal.load_asset("/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK")
    ctrl = bp.get_controller_by_name("RigVMModel")
    g = ctrl.get_graph()
    names = [n.get_name() for n in g.get_nodes()]
    for nm in ("SideRotL","SideRotR","SelSideR","SelSideL","VariableNode_3","VariableNode_4","GetRootTf"):
        if nm in names:
            ok = ctrl.remove_node_by_name(nm)
            L.append(f"CR remove {nm} -> {ok}")
    bp.recompile_vm(); bp.recompile_vm_if_required()
    ok = unreal.EditorLoadingAndSavingUtils.save_packages([bp.get_package()], False)
    L.append(f"CR save={ok}")
except Exception:
    L.append(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
