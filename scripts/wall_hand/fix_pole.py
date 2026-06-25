import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\fix_pole.txt"
DST="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
L=[]
def w(s): L.append(str(s))
try:
    bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel")
    # break live-elbow feedback into pole
    w("break "+str(ctrl.break_link("GetElbow_R.Transform.Translation","TwoBoneIK_R.PoleVector")))
    # stable pole: Direction pointing down (elbow rests downward)
    w("kind "+str(ctrl.set_pin_default_value("TwoBoneIK_R.PoleVectorKind","Direction")))
    w("vec  "+str(ctrl.set_pin_default_value("TwoBoneIK_R.PoleVector","(X=0.000000,Y=0.000000,Z=-1.000000)")))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); w("compiled")
    unreal.EditorAssetLibrary.save_asset(DST); w("saved")
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
