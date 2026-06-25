import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\dump_twobone.txt"
DST="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
L=[]
def w(s): L.append(str(s))
try:
    bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel")
    g=ctrl.get_graph()
    w("=== nodes ===")
    for n in g.get_nodes(): w("  "+n.get_node_path())
    tgt=[n for n in g.get_nodes() if n.get_node_path() in ("TwoBoneIK_R","PalmAim")]
    for n in tgt:
        w(f"\n=== {n.get_node_path()} pins (defaults) ===")
        for p in n.get_pins():
            try: w(f"  {p.get_name()} = '{p.get_default_value()}'")
            except Exception as e: w(f"  {p.get_name()} (err {e})")
    w("\n=== links touching TwoBoneIK_R / GetElbow / hand ===")
    for lk in g.get_links():
        s=lk.get_source_pin().get_pin_path(); t=lk.get_target_pin().get_pin_path()
        if any(k in s or k in t for k in ("TwoBoneIK_R","Elbow","Pole","Joint","hand","Hand")):
            w(f"  {s} -> {t}")
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
