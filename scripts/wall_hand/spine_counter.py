import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\spine_counter.txt"
DST="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
# neck/head 를 음수(카운터)로. spine 누적 +0.55 를 넘게 빼서 머리는 살짝 반대로.
TUNE=[("Mul_neck_02.B","-0.300000"),("Mul_head.B","-0.350000")]
L=[]
def w(s): L.append(str(s))
try:
    bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel")
    for p,v in TUNE:
        ok=ctrl.set_pin_default_value(p,v,False); w(("OK " if ok else "FALSE ")+p+"="+v)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); w("compiled")
    unreal.EditorAssetLibrary.save_asset(DST); w("saved")
except Exception: w(traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(L))
