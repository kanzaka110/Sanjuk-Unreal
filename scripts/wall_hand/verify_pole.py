import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\verify_pole.txt"
DST="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
L=[]
def w(s): L.append(str(s))
try:
    bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel")
    g=ctrl.get_graph()
    n=[x for x in g.get_nodes() if x.get_node_path()=="TwoBoneIK_R"][0]
    for p in n.get_pins():
        if p.get_name() in ("PoleVector","PoleVectorKind","PoleVectorSpace","Effector","Weight"):
            w(f"  {p.get_name()} = '{p.get_default_value()}'")
    w("--- live links into TwoBoneIK_R ---")
    for lk in g.get_links():
        t=lk.get_target_pin().get_pin_path()
        if "TwoBoneIK_R" in t: w(f"  {lk.get_source_pin().get_pin_path()} -> {t}")
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
