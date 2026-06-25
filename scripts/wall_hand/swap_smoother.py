import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\swap_smoother.txt"
DST="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
L=[]
def w(s): L.append(str(s))
try:
    bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel")
    g=ctrl.get_graph()
    names=[n.get_node_path() for n in g.get_nodes()]
    if "ReachDamp" in names:
        ctrl.remove_node_by_name("ReachDamp"); w("removed ReachDamp")
    if "ReachSmooth" not in [n.get_node_path() for n in g.get_nodes()]:
        node=ctrl.add_unit_node_from_struct_path("/Script/RigVM.RigVMFunction_AlphaInterpVector","Execute",unreal.Vector2D(-600,-600),"ReachSmooth")
        w(f"add ReachSmooth -> {node.get_node_path() if node else None}")
    node=[n for n in ctrl.get_graph().get_nodes() if n.get_node_path()=="ReachSmooth"][0]
    for p in node.get_pins():
        w(f"  pin '{p.get_name()}' dir={p.get_direction()} default='{p.get_default_value()}'")
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
