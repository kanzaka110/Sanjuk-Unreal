import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\diag_disable_palm.txt"
DST="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
L=[]
def w(s): L.append(str(s))
try:
    bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel")
    g=ctrl.get_graph()
    names=[n.get_node_path() for n in g.get_nodes()]
    # revert today's smoother
    if "ReachSmooth" in names:
        ctrl.break_link("ReachSmooth.Result","PalmAim.Primary.Target")
        ctrl.break_link("ReachSub.Result","ReachSmooth.Value")
        ctrl.remove_node_by_name("ReachSmooth"); w("removed ReachSmooth")
        ctrl.add_link("ReachSub.Result","PalmAim.Primary.Target"); w("restored ReachSub->PalmAim")
    # diagnostic: disable PalmAim (zero both weights)
    w("primW "+str(ctrl.set_pin_default_value("PalmAim.Primary.Weight","0.000000")))
    w("secW  "+str(ctrl.set_pin_default_value("PalmAim.Secondary.Weight","0.000000")))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); w("compiled")
    unreal.EditorAssetLibrary.save_asset(DST); w("saved")
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
