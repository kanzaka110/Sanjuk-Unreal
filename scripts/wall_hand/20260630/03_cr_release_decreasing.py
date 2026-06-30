import unreal,traceback
P="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\f525ae6b-fccb-4356-b678-43eef9ec8640\scratchpad\cr_rel.txt"
L=[]
def w(s): L.append(str(s)); open(OUT,"w").write("\n".join(L))
try:
    crb=unreal.load_asset(P)
    try: unreal.EditorAssetLibrary.checkout_loaded_asset(crb)
    except: pass
    ctrl=crb.get_controller_by_name("RigVMModel")
    for nm in("WInterpR","WInterpL"):
        ctrl.set_pin_default_value("%s.InterpSpeedDecreasing"%nm,"4.000000",False)
    crb.recompile_vm()
    ok=unreal.EditorAssetLibrary.save_asset(P,only_if_is_dirty=False); w("save=%s"%ok)
    if not ok: w("save_pkg=%s"%unreal.EditorLoadingAndSavingUtils.save_packages([crb.get_package()],False))
    g=ctrl.get_graph()
    for n in g.get_nodes():
        if n.get_node_path() in("WInterpR","WInterpL"):
            for p in n.get_pins():
                if p.get_name() in("InterpSpeedIncreasing","InterpSpeedDecreasing"): w("  %s.%s=%s"%(n.get_node_path(),p.get_name(),p.get_default_value()))
    w("DONE")
except Exception: w(traceback.format_exc())
