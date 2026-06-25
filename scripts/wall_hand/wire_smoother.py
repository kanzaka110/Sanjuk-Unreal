import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\wire_smoother.txt"
DST="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
L=[]
def w(s): L.append(str(s))
try:
    bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel")
    # enable time-interpolation (RInterpTo equivalent) on reachDir
    w("bInterp "+str(ctrl.set_pin_default_value("ReachSmooth.bInterpResult","True")))
    w("incSpd "+str(ctrl.set_pin_default_value("ReachSmooth.InterpSpeedIncreasing","12.000000")))
    w("decSpd "+str(ctrl.set_pin_default_value("ReachSmooth.InterpSpeedDecreasing","12.000000")))
    # rewire: ReachSub.Result -> [ReachSmooth.Value -> ReachSmooth.Result] -> PalmAim.Primary.Target
    w("break old "+str(ctrl.break_link("ReachSub.Result","PalmAim.Primary.Target")))
    w("link in   "+str(ctrl.add_link("ReachSub.Result","ReachSmooth.Value")))
    w("link out  "+str(ctrl.add_link("ReachSmooth.Result","PalmAim.Primary.Target")))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); w("compiled")
    unreal.EditorAssetLibrary.save_asset(DST); w("saved")
    # verify links
    for lk in ctrl.get_graph().get_links():
        s=lk.get_source_pin().get_pin_path(); t=lk.get_target_pin().get_pin_path()
        if "ReachSmooth" in s or "ReachSmooth" in t or "PalmAim.Primary.Target" in t:
            w(f"  LINK {s} -> {t}")
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
