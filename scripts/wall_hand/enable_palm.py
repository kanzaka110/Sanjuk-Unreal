import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\enable_palm.txt"
DST="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
L=[]
def w(s): L.append(str(s))
try:
    bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel")
    def sp(p,v): w(("OK " if ctrl.set_pin_default_value(p,v,False) else "FALSE ")+p+"="+v)
    sp("PalmAim.Primary.Weight","1.000000")
    sp("PalmAim.Secondary.Weight","1.000000")
    # 확인
    for n in ctrl.get_graph().get_nodes():
        if n.get_node_path()=="PalmAim":
            for pn in n.get_pins():
                if pn.get_name() in ("Primary","Secondary","Weight","Bone"): w("  "+pn.get_name()+"="+repr(pn.get_default_value()))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); w("compiled")
    unreal.EditorAssetLibrary.save_asset(DST); w("saved")
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
