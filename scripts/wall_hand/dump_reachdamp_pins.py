import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\dump_reachdamp_pins.txt"
DST="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
L=[]
def w(s): L.append(str(s))
try:
    bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel")
    g=ctrl.get_graph()
    node=None
    for n in g.get_nodes():
        if n.get_node_path()=="ReachDamp": node=n
    w(f"ReachDamp present={node is not None}")
    if node is None:
        node=ctrl.add_unit_node_from_struct_path("/Script/RigVM.RigVMFunction_DampVector","Execute",unreal.Vector2D(-600,-600),"ReachDamp")
        w("re-added ReachDamp")
    for p in node.get_pins():
        w(f"  pin '{p.get_name()}' dir={p.get_direction()} default='{p.get_default_value()}'")
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
