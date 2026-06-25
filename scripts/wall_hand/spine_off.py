import unreal
DST="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel")
for nm in ("SpineAim_02","SpineAim_03"):
    ctrl.set_pin_default_value(nm+".Primary.Weight","0.000000",False)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
unreal.EditorAssetLibrary.save_asset(DST)
open(r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\spineoff.txt","w").write("spine weight=0, compiled+saved")
