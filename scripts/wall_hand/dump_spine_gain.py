import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\dump_spine_gain.txt"
DST="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
L=[]
def w(s): L.append(str(s))
try:
    bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel")
    g=ctrl.get_graph()
    want=["MulK","Yaw","Mul_spine_02","Mul_spine_03","Mul_neck_02","Mul_head"]
    for nm in want:
        n=[x for x in g.get_nodes() if x.get_node_path()==nm]
        if not n: w(f"{nm}: MISSING"); continue
        n=n[0]
        w(f"=== {nm}  ({n.get_node_path()}) ===")
        for p in n.get_pins():
            d=p.get_direction()
            if str(d).endswith("INPUT: 0>"):
                w(f"   {p.get_name()} = '{p.get_default_value()}'")
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
