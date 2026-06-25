import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\reach_chest.txt"
DST="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
L=[]
def w(s): L.append(str(s))
try:
    bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel")
    # reachDir origin: swinging upperarm -> stable chest(spine_03 via SpineRef)
    ok1=ctrl.break_link("GetUpper_R.Transform.Translation","ReachSub.B"); w(f"break Upper->ReachSub.B ({ok1})")
    ok2=ctrl.add_link("SpineRef.Transform.Translation","ReachSub.B"); w(f"link SpineRef.Translation->ReachSub.B ({ok2})")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); w("compiled")
    unreal.EditorAssetLibrary.save_asset(DST); w("saved")
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
