import unreal, traceback
OUT=r"C:\Users\SHIFTUP\AppData\Local\Temp\claude\C--Dev-Sanjuk-Unreal\afc97dd6-1b24-41ae-b1e1-10943ed3c5d4\scratchpad\reconnect_pole.txt"
DST="/Game/Art/Character/PC/PC_01/Rig/PC_01_CtrlRig_WallHandIK"
lines=[]
def w(s): lines.append(str(s))
try:
    bp=unreal.load_asset(DST); ctrl=bp.get_controller_by_name("RigVMModel")
    # Kind 다시 Location
    ctrl.set_pin_default_value("TwoBoneIK_R.PoleVectorKind","Location",False); w("Kind=Location")
    # GetElbow 재연결
    ok=ctrl.add_link("GetElbow_R.Transform.Translation","TwoBoneIK_R.PoleVector"); w(f"link GetElbow->PoleVector ({ok})")
    unreal.BlueprintEditorLibrary.compile_blueprint(bp); w("compiled")
    unreal.EditorAssetLibrary.save_asset(DST); w("saved")
    # 확인
    g=ctrl.get_graph()
    for lk in g.get_links():
        if "PoleVector" in lk.get_target_pin().get_pin_path(): w("LINK: "+lk.get_source_pin().get_pin_path()+" -> "+lk.get_target_pin().get_pin_path())
except Exception:
    w("ERR "+traceback.format_exc())
open(OUT,"w",encoding="utf-8").write("\n".join(lines))
